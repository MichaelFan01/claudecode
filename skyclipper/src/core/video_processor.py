#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video processing pipeline orchestration module.

This module provides the main pipeline orchestration for video processing,
coordinating TransNet scene detection and Qwen3-VL action recognition.
"""

import os
import sys
import gc
import time
import json
import signal
from datetime import datetime
from multiprocessing import Queue, Process, Manager
from queue import Empty

import torch
import torch.multiprocessing as mp
import pandas as pd
from tqdm import tqdm
from vllm import LLM, SamplingParams
from transformers import AutoProcessor

from src.utils.json_utils import fast_json_dumps
from src.utils.time_utils import time_to_seconds
from src.utils.xml_parser import parse_xml_clips
from src.core.scene_detector import transnet_producer, TransNetWorker
from src.core.action_recognizer import (
    prepare_video_data,
    prepare_video_data_wrapper,
    load_prompt_template,
    frame_to_timestamp
)


# Global process list for signal handling
ALL_PROCESSES = []


def signalHandler(signum, frame):
    """Handle Ctrl+C signals and clean up all child processes."""
    print("\n\n⚠️  Received termination signal, cleaning up all processes...")
    for p in ALL_PROCESSES:
        try:
            p.terminate()
        except:
            pass
    time.sleep(2)
    for p in ALL_PROCESSES:
        try:
            p.kill()
        except:
            pass
    print("✓ All processes terminated")
    sys.exit(0)


def qwen3VLConsumer(resultQueue, outputFile, args, totalVideos=0):
    """
    Qwen3-VL consumer: takes videos from result queue and performs batch inference.

    Args:
        resultQueue: Queue to get processed video results from
        outputFile: Path to output file
        args: Configuration arguments
        totalVideos: Total number of videos to process
    """
    print(f"\n{'='*80}")
    print(f"[Qwen3-VL] Starting... [time: {datetime.now().strftime('%H:%M:%S')}]")
    print(f"{'='*80}")

    print(f"[Qwen3-VL] Loading model (this may take 1-2 minutes)... [time: {datetime.now().strftime('%H:%M:%S')}]")
    modelLoadStart = time.time()
    samplingParams = SamplingParams(temperature=0.7, max_tokens=4096)

    llm = LLM(
        model=args.model_path,
        mm_encoder_tp_mode="data",
        gpu_memory_utilization=0.9,
        tensor_parallel_size=8,
        dtype=torch.bfloat16,
        max_model_len=30000,
        disable_custom_all_reduce=True,
        max_num_seqs=args.batch_size,
    )

    processor = AutoProcessor.from_pretrained(args.model_path, local_files_only=True)
    modelLoadTime = time.time() - modelLoadStart

    print(f"\n{'='*80}")
    print(f"[Qwen3-VL] ✓ Model loaded! Took {modelLoadTime:.1f}s [time: {datetime.now().strftime('%H:%M:%S')}]")
    print(f"[Qwen3-VL] 📝 Batch strategy:")
    maxWaitTime = 10
    print(f"  • Collect {args.queue_batch_size} videos → process immediately ⚡")
    print(f"  • TransNet slowdown (2s no new videos) → process collected")
    print(f"  • Exceed {maxWaitTime}s → force process")
    try:
        queueSize = resultQueue.qsize()
        print(f"[Qwen3-VL] 📊 Current result_queue size: {queueSize}")
    except:
        print(f"[Qwen3-VL] 📊 result_queue initialized (qsize unavailable)")
    print(f"[Qwen3-VL] 🎬 Starting work (parallel with TransNet)...")
    print(f"{'='*80}\n")

    processedVideos = 0
    pendingTasks = []
    lastBatchTime = time.time()
    lastStatusTime = time.time()
    loopCount = 0

    print(f"[Qwen3-VL DEBUG] Entering main loop [time: {datetime.now().strftime('%H:%M:%S')}]")

    with open(outputFile, 'w', encoding='utf-8') as f:
        while True:
            loopCount += 1
            if loopCount % 100 == 0:
                try:
                    queueSize = resultQueue.qsize()
                    print(f"[Qwen3-VL DEBUG] Heartbeat #{loopCount}, queue_size={queueSize}, pending={len(pendingTasks)} [time: {datetime.now().strftime('%H:%M:%S')}]")
                except:
                    print(f"[Qwen3-VL DEBUG] Heartbeat #{loopCount}, pending={len(pendingTasks)} [time: {datetime.now().strftime('%H:%M:%S')}]")

            try:
                getStart = time.time()
                print(f"[Qwen3-VL DEBUG] Trying to get task from queue (timeout=2s)... [time: {datetime.now().strftime('%H:%M:%S')}]")
                task = resultQueue.get(timeout=2)
                getTime = time.time() - getStart
                print(f"[Qwen3-VL DEBUG] ✓ Got task successfully, took {getTime:.3f}s [time: {datetime.now().strftime('%H:%M:%S')}]")

                if task is None:
                    print(f"[Qwen3-VL] Received stop signal [time: {datetime.now().strftime('%H:%M:%S')}]")
                    if pendingTasks:
                        print(f"[Qwen3-VL] Processing remaining {len(pendingTasks)} tasks...")
                        processBatch(pendingTasks, llm, processor, samplingParams, f, args, processedVideos, totalVideos)
                    break

                videoId, videoPath, transnetPath, scenes, fromCache, videoMetadata = task
                print(f"[Qwen3-VL] ← Received video: {videoId}, {len(scenes)} scenes, cached={fromCache} [time: {datetime.now().strftime('%H:%M:%S')}]")

                if not scenes or len(scenes) == 0:
                    print(f"[Qwen3-VL] ⚠️  Skipping {videoId}: no scene data (file may not exist)")
                    continue

                pendingTasks.append((videoId, videoPath, transnetPath, scenes, videoMetadata))
                print(f"[Qwen3-VL] ✓ Added to pending_tasks, current queue: {len(pendingTasks)}/{args.queue_batch_size} [time: {datetime.now().strftime('%H:%M:%S')}]")

                if time.time() - lastStatusTime >= 5 and len(pendingTasks) < args.queue_batch_size:
                    timeWaited = int(time.time() - lastBatchTime)
                    print(f"[Qwen3-VL] Waiting... Collected {len(pendingTasks)}/{args.queue_batch_size} videos (waited {timeWaited}s) [time: {datetime.now().strftime('%H:%M:%S')}]")
                    lastStatusTime = time.time()

                timeSinceLastBatch = time.time() - lastBatchTime
                shouldProcess = (
                    len(pendingTasks) >= args.queue_batch_size or
                    (len(pendingTasks) > 0 and timeSinceLastBatch >= maxWaitTime)
                )

                print(f"[Qwen3-VL DEBUG] Checking if should process: pending={len(pendingTasks)}, wait_time={timeSinceLastBatch:.1f}s, should_process={shouldProcess}")

                if shouldProcess:
                    if len(pendingTasks) >= args.queue_batch_size:
                        triggerReason = f"Queue full ({len(pendingTasks)} videos)"
                    else:
                        triggerReason = f"Exceeded max wait time ({int(timeSinceLastBatch)}s)"
                    print(f"[Qwen3-VL] → Triggering batch processing: {triggerReason} [time: {datetime.now().strftime('%H:%M:%S')}]\n")

                    batchStart = time.time()
                    processBatch(pendingTasks, llm, processor, samplingParams, f, args, processedVideos, totalVideos)
                    batchTime = time.time() - batchStart
                    print(f"[Qwen3-VL DEBUG] ✓ Batch processing complete, took {batchTime:.1f}s [time: {datetime.now().strftime('%H:%M:%S')}]")

                    processedVideos += len(pendingTasks)
                    pendingTasks = []
                    lastBatchTime = time.time()
                    lastStatusTime = time.time()

            except Empty:
                print(f"[Qwen3-VL DEBUG] Queue.get() timeout (2s no new data), pending={len(pendingTasks)} [time: {datetime.now().strftime('%H:%M:%S')}]")
                if pendingTasks:
                    timeWaited = int(time.time() - lastBatchTime)
                    print(f"[Qwen3-VL] → Triggering batch processing: TransNet slowdown, processing collected {len(pendingTasks)} videos [time: {datetime.now().strftime('%H:%M:%S')}]\n")

                    batchStart = time.time()
                    processBatch(pendingTasks, llm, processor, samplingParams, f, args, processedVideos, totalVideos)
                    batchTime = time.time() - batchStart
                    print(f"[Qwen3-VL DEBUG] ✓ Batch processing complete, took {batchTime:.1f}s [time: {datetime.now().strftime('%H:%M:%S')}]")

                    processedVideos += len(pendingTasks)
                    pendingTasks = []
                    lastBatchTime = time.time()
                    lastStatusTime = time.time()
                else:
                    print(f"[Qwen3-VL DEBUG] pending_tasks empty, continuing to wait... [time: {datetime.now().strftime('%H:%M:%S')}]")
            except Exception as e:
                print(f"[Qwen3-VL] Error: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()

    print(f"\n{'='*80}")
    print(f"[Qwen3-VL] ✓ All video processing complete: {processedVideos}/{totalVideos} videos")
    print(f"{'='*80}")


def processBatch(tasks, llm, processor, samplingParams, outputFile, args, processedCount=0, totalVideos=0):
    """
    Batch process videos - actual batch inference (by segments) + parallel data preparation.

    Args:
        tasks: List of tasks to process
        llm: VLLM model instance
        processor: Qwen3-VL processor
        samplingParams: VLLM sampling parameters
        outputFile: Output file object
        args: Configuration arguments
        processedCount: Number of already processed videos
        totalVideos: Total number of videos to process
    """
    if not tasks:
        return

    progressStr = f"{processedCount}/{totalVideos}" if totalVideos > 0 else f"{processedCount}"
    print(f"\n{'='*80}")
    print(f"[Qwen3-VL] 🎬 Processing video batch: {len(tasks)} videos (total progress: {progressStr}) [time: {datetime.now().strftime('%H:%M:%S')}]")
    print(f"{'='*80}")

    allSegments = []

    numWorkers = min(16, len(tasks), mp.cpu_count())

    print(f"  → Preparing data: using {numWorkers} parallel workers to load video frames... [time: {datetime.now().strftime('%H:%M:%S')}]")
    prepareStart = time.time()

    videoMetadataMap = {}
    for item in tasks:
        videoId, videoPath, transnetPath, transnetScenes, videoMetadata = item
        videoMetadataMap[videoId] = videoMetadata

    prepareArgs = [
        (videoId, videoPath, transnetPath, transnetScenes, args.model_path, args)
        for videoId, videoPath, transnetPath, transnetScenes, videoMetadata in tasks
    ]

    try:
        with mp.Pool(processes=numWorkers) as pool:
            results = []
            for idx, videoData in enumerate(pool.imap_unordered(prepare_video_data_wrapper, prepareArgs)):
                if videoData is not None:
                    results.append(videoData)
                    print(f"[Qwen3-VL] ✓ Video preparation complete {len(results)}/{len(tasks)}: {videoData['video_id']}, {len(videoData['segments'])} segments")
                else:
                    print(f"[Qwen3-VL] ⚠️  Video preparation failed (skipping)")
    except Exception as e:
        print(f"[Qwen3-VL] Parallel processing failed, falling back to sequential: {e}")
        results = []
        for videoId, videoPath, transnetPath, transnetScenes, videoMetadata in tasks:
            try:
                videoData = prepare_video_data(videoId, videoPath, transnetPath, transnetScenes, processor, args)
                if videoData:
                    results.append(videoData)
            except Exception as e2:
                print(f"[Qwen3-VL] Error preparing {videoId}: {e2}")

    for videoData in results:
        videoId = videoData['video_id']
        metadata = videoMetadataMap.get(videoId, {})
        for segIdx, segData in enumerate(videoData['segments']):
            allSegments.append((
                videoId,
                videoData['video_path'],
                videoData['transnet_path'],
                segIdx,
                len(videoData['segments']),
                segData['inputs'],
                segData['segment_info'],
                videoData['video_meta'],
                metadata
            ))

    prepareTime = time.time() - prepareStart
    speedup = len(tasks) * 142 / prepareTime if prepareTime > 0 else 1
    print(f"  Complete ({prepareTime:.1f}s) [time: {datetime.now().strftime('%H:%M:%S')}]")
    print(f"  → Parallel speedup: estimated {speedup:.1f}x (would have taken {len(tasks)*142:.0f}s)")
    print(f"  → Collected {len(allSegments)} segments, starting inference... [time: {datetime.now().strftime('%H:%M:%S')}]")

    totalBatches = (len(allSegments) + args.batch_size - 1) // args.batch_size
    print(f"[Qwen3-VL DEBUG] Will inference in {totalBatches} batches, max {args.batch_size} segments per batch")

    totalInferenceTime = 0
    for batchIdx in range(0, len(allSegments), args.batch_size):
        batchEnd = min(batchIdx + args.batch_size, len(allSegments))
        batchSegments = allSegments[batchIdx:batchEnd]

        currentBatch = batchIdx//args.batch_size + 1
        print(f"\n[Qwen3-VL DEBUG] === Batch {currentBatch}/{totalBatches} starting === [time: {datetime.now().strftime('%H:%M:%S')}]")
        print(f"  → [{currentBatch}/{totalBatches}] Inferencing {len(batchSegments)} segments...", flush=True)

        try:
            print(f"[Qwen3-VL DEBUG] Preparing batch inputs...")
            prepareBatchStart = time.time()
            batchInputs = [seg[5] for seg in batchSegments]
            prepareBatchTime = time.time() - prepareBatchStart
            print(f"[Qwen3-VL DEBUG] ✓ Batch inputs prepared, took {prepareBatchTime:.3f}s")

            if currentBatch > 1 and totalInferenceTime > 0:
                completedSegments = batchIdx
                remainingSegments = len(allSegments) - batchEnd
                avgTimePerSegment = totalInferenceTime / completedSegments
                estimatedRemainingTime = remainingSegments * avgTimePerSegment

                if estimatedRemainingTime < 60:
                    timeStr = f"{estimatedRemainingTime:.0f}s"
                elif estimatedRemainingTime < 3600:
                    mins = int(estimatedRemainingTime / 60)
                    secs = int(estimatedRemainingTime % 60)
                    timeStr = f"{mins}m{secs}s"
                else:
                    hours = int(estimatedRemainingTime / 3600)
                    mins = int((estimatedRemainingTime % 3600) / 60)
                    timeStr = f"{hours}h{mins}m"

                print(f"[Qwen3-VL] ⏱️  Estimated time remaining: {timeStr} ({remainingSegments} segments left, avg {avgTimePerSegment:.1f}s/segment)")

            print(f"[Qwen3-VL DEBUG] Starting LLM inference... [time: {datetime.now().strftime('%H:%M:%S')}]")
            startTime = time.time()
            outputs = llm.generate(batchInputs, samplingParams, use_tqdm=False)
            elapsed = time.time() - startTime
            totalInferenceTime += elapsed

            print(f"[Qwen3-VL DEBUG] ✓ LLM inference complete [time: {datetime.now().strftime('%H:%M:%S')}]")
            print(f"  ✓ {elapsed:.1f}s ({len(batchSegments)/elapsed:.2f} seg/s)")

            print(f"[Qwen3-VL DEBUG] Parsing and saving {len(outputs)} results...")
            saveStart = time.time()
            for idx, (output, segData) in enumerate(zip(outputs, batchSegments)):
                videoId, videoPath, transnetPath, segIdx, numSegments, inputs, segmentInfo, videoMeta, metadata = segData
                llmOutput = output.outputs[0].text

                clips = []
                try:
                    clips = parse_xml_clips(llmOutput)
                    fps = videoMeta['fps']
                    segmentStartFrame = segmentInfo['start_frame']
                    for clip in clips:
                        try:
                            startSeconds = time_to_seconds(clip['start_time'])
                            endSeconds = time_to_seconds(clip['end_time'])
                            clip['start_frame'] = segmentStartFrame + int(startSeconds * fps)
                            clip['end_frame'] = segmentStartFrame + int(endSeconds * fps)
                        except Exception as e:
                            print(f"[Qwen3-VL] Warning: Failed to calculate frames for clip: {e}")
                            clip['start_frame'] = 0
                            clip['end_frame'] = 0
                except:
                    pass

                result = {
                    'id': videoId,
                    'segment_id': f"{videoId}_seg{segIdx}",
                    'segment_index': segIdx,
                    'num_segments': numSegments,
                    'video_path': videoPath,
                    'transnet_path': transnetPath,
                    'llm_output': llmOutput,
                    'clips': clips,
                    'video_meta': videoMeta,
                    'segment_info': segmentInfo
                }

                result.update(metadata)

                outputFile.write(fast_json_dumps(result) + '\n')

            saveTime = time.time() - saveStart
            print(f"[Qwen3-VL DEBUG] ✓ Results saved, took {saveTime:.2f}s")

            outputFile.flush()

            completedSegments = batchEnd
            progressPct = (completedSegments / len(allSegments)) * 100
            remainingBatches = totalBatches - currentBatch

            print(f"[Qwen3-VL DEBUG] === Batch {currentBatch}/{totalBatches} complete === [time: {datetime.now().strftime('%H:%M:%S')}]")
            print(f"  📊 Overall progress: {completedSegments}/{len(allSegments)} segments ({progressPct:.1f}%), {remainingBatches} batches left\n")

        except Exception as e:
            print(f"[Qwen3-VL] Batch inference error: {e} [time: {datetime.now().strftime('%H:%M:%S')}]")
            import traceback
            traceback.print_exc()
            for segData in batchSegments:
                videoId, videoPath, transnetPath, segIdx, numSegments, inputs, segmentInfo, videoMeta, metadata = segData
                try:
                    outputs = llm.generate([inputs], samplingParams, use_tqdm=False)
                    llmOutput = outputs[0].outputs[0].text
                    clips = []
                    try:
                        clips = parse_xml_clips(llmOutput)
                        fps = videoMeta['fps']
                        segmentStartFrame = segmentInfo['start_frame']
                        for clip in clips:
                            try:
                                startSeconds = time_to_seconds(clip['start_time'])
                                endSeconds = time_to_seconds(clip['end_time'])
                                clip['start_frame'] = segmentStartFrame + int(startSeconds * fps)
                                clip['end_frame'] = segmentStartFrame + int(endSeconds * fps)
                            except Exception as e:
                                print(f"[Qwen3-VL] Warning: Failed to calculate frames for clip: {e}")
                                clip['start_frame'] = 0
                                clip['end_frame'] = 0
                    except:
                        pass
                    result = {
                        'id': videoId,
                        'segment_id': f"{videoId}_seg{segIdx}",
                        'segment_index': segIdx,
                        'num_segments': numSegments,
                        'video_path': videoPath,
                        'transnet_path': transnetPath,
                        'llm_output': llmOutput,
                        'clips': clips,
                        'video_meta': videoMeta,
                        'segment_info': segmentInfo
                    }
                    result.update(metadata)
                    outputFile.write(fast_json_dumps(result) + '\n')
                except Exception as e2:
                    print(f"[Qwen3-VL] Error processing segment {videoId}_seg{segIdx}: {e2}")
            outputFile.flush()

    print(f"[Qwen3-VL DEBUG] Starting memory cleanup... [time: {datetime.now().strftime('%H:%M:%S')}]")
    cleanupStart = time.time()
    del allSegments
    gc.collect()
    torch.cuda.empty_cache()
    cleanupTime = time.time() - cleanupStart
    print(f"[Qwen3-VL DEBUG] ✓ Memory cleanup complete, took {cleanupTime:.2f}s")

    newProcessed = processedCount + len(tasks)
    progressStr = f"{newProcessed}/{totalVideos}" if totalVideos > 0 else f"{newProcessed}"
    progressPct = f"({100*newProcessed/totalVideos:.1f}%)" if totalVideos > 0 else ""
    avgTimePerVideo = totalInferenceTime / len(tasks) if len(tasks) > 0 else 0
    print(f"  ✓ Batch complete: {len(tasks)} videos, total inference {totalInferenceTime:.1f}s (avg {avgTimePerVideo:.1f}s/video)")
    print(f"  ✓ Total progress: {progressStr} {progressPct}")
    print(f"{'='*80}\n")
    print(f"[processBatch] ✓ Complete [time: {datetime.now().strftime('%H:%M:%S')}]\n")


def processVideoPipeline(videoList, outputJsonl, args):
    """
    Main video processing pipeline orchestration.

    Args:
        videoList: Path to video list CSV file
        outputJsonl: Path to output JSONL file
        args: Configuration arguments
    """
    signal.signal(signal.SIGINT, signalHandler)
    signal.signal(signal.SIGTERM, signalHandler)

    outputDir = os.path.dirname(outputJsonl)
    os.makedirs(outputDir, exist_ok=True)

    tempDir = outputJsonl.replace(".jsonl", "_temp")
    os.makedirs(tempDir, exist_ok=True)

    if args.transnet_cache_dir is None:
        args.transnet_cache_dir = outputJsonl.replace(".jsonl", "_transnet")
    os.makedirs(args.transnet_cache_dir, exist_ok=True)

    outPath = os.path.join(tempDir, f"node_{args.node_rank}.jsonl")

    print(f"\n{'='*80}")
    print(f"🎬 Parallel Video Processing (TransNet + Qwen3-VL)")
    print(f"{'='*80}")
    print(f"📊 Configuration:")
    print(f"  • GPU allocation:")
    print(f"    - TransNet: {args.transnet_workers} workers (~10%/GPU)")
    print(f"    - Qwen3-VL: 8 GPUs @ 90% memory")
    print(f"  • Batch strategy:")
    print(f"    - Video batches: {args.videos_per_batch} videos/batch")
    print(f"    - Queue batches: {args.queue_batch_size} videos → trigger processing")
    print(f"    - Inference batches: {args.batch_size} segments/time")
    print(f"  • Output file: {outPath}")
    if args.resume:
        print(f"  • Resume mode: enabled")
    print(f"{'='*80}\n")

    df = pd.read_csv(videoList)
    if 'id' not in df.columns:
        import hashlib
        df['id'] = df['path'].apply(lambda x: hashlib.md5(x.encode()).hexdigest()[:12])

    totalVideos = len(df)
    videosPerNode = totalVideos // args.num_nodes
    startIdx = args.node_rank * videosPerNode
    endIdx = startIdx + videosPerNode if args.node_rank < args.num_nodes - 1 else totalVideos
    nodeDf = df.iloc[startIdx:endIdx]

    print(f"Node {args.node_rank}: {len(nodeDf)} videos (rows {startIdx}-{endIdx-1})")

    processedIds = set()
    if args.resume and os.path.exists(outPath):
        print(f"Resume mode: checking processed videos...")
        with open(outPath, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    processedIds.add(data['id'])
                except:
                    pass
        print(f"  → Already processed {len(processedIds)} videos, will skip")
        nodeDf = nodeDf[~nodeDf['id'].isin(processedIds)]
        print(f"  → {len(nodeDf)} videos remaining to process")

    totalVideosToProcess = len(nodeDf)

    print(f"\n📊 Processing tasks:")
    print(f"  → Videos to process: {totalVideosToProcess}")
    print(f"  → Strategy: TransNet parallel processing → Qwen3-VL batch inference\n")

    manager = Manager()
    videoQueue = manager.Queue()
    resultQueue = manager.Queue()

    print(f"\n{'='*80}")
    print(f"[1/2] Starting TransNet producer processes...")
    print(f"{'='*80}")

    transnetProcesses = []
    numGpus = torch.cuda.device_count() if torch.cuda.is_available() else 1
    print(f"  → TransNet: {args.transnet_workers} workers (GPU 0-{numGpus-1})")

    for i in range(args.transnet_workers):
        p = Process(target=transnet_producer, args=(
            i, videoQueue, resultQueue, args.transnet_weights,
            args.transnet_threshold, args.transnet_cache_dir, numGpus, args.transnet_workers
        ))
        p.start()
        transnetProcesses.append(p)
        ALL_PROCESSES.append(p)

    print(f"  ✓ TransNet processes started\n")

    print(f"{'='*80}")
    print(f"[2/2] Starting Qwen3-VL consumer process...")
    print(f"{'='*80}")
    print(f"  → Qwen3-VL: 8 GPUs @ 90% memory")
    print(f"  → This may take 1-2 minutes to load the model...\n")

    consumerProcess = Process(target=qwen3VLConsumer, args=(resultQueue, outPath, args, totalVideosToProcess))
    consumerProcess.start()
    ALL_PROCESSES.append(consumerProcess)

    print(f"{'='*80}")
    print(f"[Pipeline] 🎬 Pipeline started - running in parallel:")
    print(f"  1️⃣  TransNet workers: process videos → result_queue")
    print(f"  2️⃣  Qwen3-VL consumer: read from result_queue → batch inference")
    print(f"  3️⃣  Main process: feed tasks, then wait for completion")
    print(f"{'='*80}\n")

    print(f"📤 [Main process] Feeding {totalVideosToProcess} videos to video_queue...")

    feedCount = 0
    for _, row in nodeDf.iterrows():
        videoId = row['id']
        videoPath = row['path']
        transnetPath = os.path.join(args.transnet_cache_dir, f"{videoId}.scenes.txt")

        videoMetadata = {}
        for field in ['name', 'studio', 'genres', 'art_style', 'year_range', 'type', 'duration']:
            if field in row and pd.notna(row[field]):
                videoMetadata[field] = row[field]

        videoQueue.put((videoId, videoPath, transnetPath, videoMetadata))
        feedCount += 1

    print(f"✓ [Main process] Fed {feedCount} videos")
    print(f"📊 [Main process] TransNet and Qwen3-VL working in parallel...\n")

    for _ in range(args.transnet_workers):
        videoQueue.put(None)

    print(f"\n{'='*80}")
    print(f"⏳ [Main process] Waiting for pipeline to complete...")
    print(f"   (TransNet and Qwen3-VL working in parallel in the background)")
    print(f"{'='*80}\n")

    for p in transnetProcesses:
        p.join()
    print(f"✓ [Main process] All TransNet workers complete")

    consumerProcess.join()
    print(f"✓ [Main process] Qwen3-VL consumer complete")

    print(f"\n{'='*80}")
    print(f"🎉 All processing complete!")
    print(f"{'='*80}")
    print(f"Output file: {outPath}")
    if args.resume:
        print(f"Tip: Use --resume to continue processing more videos")
    print(f"{'='*80}")


# Snake_case aliases for backward compatibility
signal_handler = signalHandler
qwen3vl_consumer = qwen3VLConsumer
process_batch = processBatch
process_video_pipeline = processVideoPipeline
