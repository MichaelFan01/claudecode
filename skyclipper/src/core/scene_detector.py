#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scene detection module using TransNetV2.

This module provides scene detection functionality using the TransNetV2 model
for video scene boundary detection.
"""

import os
import sys
import time
import contextlib
import warnings

import torch
import numpy as np

# TransNet imports
try:
    from transnetv2_pytorch import TransNetV2
    TRANSNET_AVAILABLE = True
except ImportError:
    TRANSNET_AVAILABLE = False


@contextlib.contextmanager
def suppressFfmpegLogs():
    """Suppress FFmpeg log output (including h264 warnings)."""
    original_stderr = sys.stderr

    try:
        sys.stderr = open(os.devnull, 'w')
        yield
    finally:
        sys.stderr.close()
        sys.stderr = original_stderr


class TransNetWorker:
    """TransNet worker process for scene detection."""

    def __init__(self, workerId, weightsPath, threshold=0.3, device='cuda'):
        """
        Initialize TransNet worker.

        Args:
            workerId: Worker identifier
            weightsPath: Path to TransNet weights file
            threshold: Scene detection threshold (default: 0.3)
            device: Device to run on ('cuda' or 'cpu')
        """
        self.workerId = workerId
        self.weightsPath = weightsPath
        self.threshold = threshold
        self.device = device
        self.model = None

    def initialize(self):
        """
        Initialize TransNet model.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        if not TRANSNET_AVAILABLE:
            return False

        try:
            self.model = TransNetV2()

            stateDict = torch.load(self.weightsPath, map_location='cpu', weights_only=True)
            self.model.load_state_dict(stateDict)
            self.model.eval()
            self.model = self.model.to(self.device)

            return True
        except Exception as e:
            print(f"[TransNet-{self.workerId}] Failed to initialize: {e}")
            import traceback
            traceback.print_exc()
            return False

    def processVideo(self, videoPath):
        """
        Process a single video and return scene boundaries.

        Args:
            videoPath: Path to video file

        Returns:
            list: List of (start_frame, end_frame) tuples representing scenes
        """
        if self.model is None:
            print(f"[TransNet-{self.workerId}] ERROR: Model is None!")
            return []

        if not os.path.exists(videoPath):
            print(f"[TransNet-{self.workerId}] ERROR: Video file not found: {videoPath}")
            return []

        try:
            import io
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()

            try:
                videoFrames, singleFramePredictions, allFramePredictions = \
                    self.model.predict_video(str(videoPath))
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            singleFrameNp = singleFramePredictions.cpu().numpy() if isinstance(singleFramePredictions, torch.Tensor) else singleFramePredictions
            allFrameNp = allFramePredictions.cpu().numpy() if isinstance(allFramePredictions, torch.Tensor) else allFramePredictions

            scenes = self.model.predictions_to_scenes(singleFrameNp, threshold=self.threshold)
            scenesList = scenes.tolist() if hasattr(scenes, 'tolist') else scenes

            return scenesList
        except Exception as e:
            import traceback
            print(f"[TransNet-{self.workerId}] ERROR processing video {os.path.basename(videoPath)}: {e}")
            print(f"[TransNet-{self.workerId}] Traceback: {traceback.format_exc()}")
            return []


def transnetProducer(workerId, videoQueue, resultQueue, transnetWeights,
                     transnetThreshold, cacheDir, numGpus=8, totalWorkers=8):
    """
    TransNet producer process: takes videos from queue, processes them, and puts results in result queue.

    Args:
        workerId: Worker identifier
        videoQueue: Queue to get video tasks from
        resultQueue: Queue to put results in
        transnetWeights: Path to TransNet weights
        transnetThreshold: Scene detection threshold
        cacheDir: Directory to cache TransNet results
        numGpus: Number of GPUs available
        totalWorkers: Total number of TransNet workers
    """
    gpuId = workerId % numGpus
    os.environ['CUDA_VISIBLE_DEVICES'] = str(gpuId)

    if workerId == 0:
        print(f"[TransNet] Starting {totalWorkers} workers on GPUs 0-{numGpus-1}...")

    device = 'cuda:0'

    worker = TransNetWorker(workerId, transnetWeights, transnetThreshold, device=device)
    if not worker.initialize():
        print(f"[TransNet-{workerId}] Initialization failed, exiting")
        return

    processedCount = 0

    from queue import Empty

    while True:
        try:
            task = videoQueue.get(timeout=5)

            if task is None:
                print(f"[TransNet-{workerId}] Received stop signal, processed {processedCount} videos")
                print(f"[TransNet-{workerId}] Sending stop signal to Qwen3-VL")
                resultQueue.put(None)
                break

            videoId, videoPath, transnetPath, videoMetadata = task

            if os.path.exists(transnetPath):
                scenes = []
                try:
                    with open(transnetPath, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith('#'):
                                continue
                            parts = line.split()
                            if len(parts) >= 2:
                                scenes.append((int(parts[0]), int(parts[1])))
                except:
                    scenes = []

                resultQueue.put((videoId, videoPath, transnetPath, scenes, True, videoMetadata))
                processedCount += 1
                print(f"[TransNet-{workerId}] {videoId}: Read {len(scenes)} scenes from cache, added to result_queue")
                continue

            if not os.path.exists(videoPath):
                print(f"[TransNet-{workerId}] ERROR: Video file not found: {videoPath}")
                resultQueue.put((videoId, videoPath, transnetPath, [], False, videoMetadata))
                processedCount += 1
                continue

            startTime = time.time()
            scenes = worker.processVideo(videoPath)
            elapsed = time.time() - startTime

            os.makedirs(os.path.dirname(transnetPath), exist_ok=True)
            try:
                with open(transnetPath, 'w') as f:
                    f.write(f"# TransNet V2 scene boundaries\n")
                    for startFrame, endFrame in scenes:
                        f.write(f"{startFrame} {endFrame}\n")
            except Exception as e:
                print(f"[TransNet-{workerId}] Failed to save cache: {e}")

            from datetime import datetime
            print(f"[TransNet-{workerId}] Adding to result_queue: {videoId}, {len(scenes)} scenes [time: {datetime.now().strftime('%H:%M:%S')}]")
            putStart = time.time()
            resultQueue.put((videoId, videoPath, transnetPath, scenes, False, videoMetadata))
            putTime = time.time() - putStart
            processedCount += 1
            try:
                queueSize = resultQueue.qsize()
                print(f"[TransNet-{workerId}] Added to result_queue (took {putTime:.3f}s), current queue size: {queueSize}")
            except:
                print(f"[TransNet-{workerId}] Added to result_queue (took {putTime:.3f}s)")

            if len(scenes) == 0:
                print(f"[TransNet-{workerId}] WARNING: {videoId} - NO SCENES DETECTED in {elapsed:.2f}s")

        except Empty:
            continue
        except Exception as e:
            print(f"[TransNet-{workerId}] Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            continue


# Snake_case aliases for backward compatibility
suppress_ffmpeg_logs = suppressFfmpegLogs
transnet_producer = transnetProducer
