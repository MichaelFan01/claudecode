#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Action recognition module using Qwen3-VL.

This module provides action recognition functionality using the Qwen3-VL
visual-language model for video analysis and clip extraction.
"""

import os
import re
import time
import warnings
import contextlib
from datetime import datetime
from pathlib import Path

import torch
import numpy as np
import decord

from src.utils.time_utils import time_to_seconds, seconds_to_time
from src.utils.xml_parser import parse_xml_clips


# Global flag for whether to merge adjacent same-action clips
USE_MERGE_ACTION_CLIPS = os.environ.get('SKYCLIPPER_USE_MERGE', '0') in ('1', 'true', 'True')


@contextlib.contextmanager
def suppressFfmpegLogs():
    """Suppress FFmpeg log output (including h264 warnings)."""
    import sys
    original_stderr = sys.stderr

    try:
        sys.stderr = open(os.devnull, 'w')
        yield
    finally:
        sys.stderr.close()
        sys.stderr = original_stderr


def loadPromptTemplate(videoPath):
    """
    Load prompt template based on video filename.

    Args:
        videoPath: Path to video file

    Returns:
        str: Loaded prompt template
    """
    videoFilename = os.path.basename(videoPath)
    if videoFilename.startswith('zh_'):
        promptFile = 'data/prompt-templates/prompt_template_action_zh.txt'
    else:
        promptFile = 'data/prompt-templates/prompt_template_action_en.txt'

    try:
        with open(promptFile, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "Please analyze this video and provide a description."


def frameToTimestamp(frame, fps):
    """
    Convert frame number to timestamp string in HH:MM:SS,mmm format.

    Args:
        frame: Frame number
        fps: Frames per second

    Returns:
        str: Formatted timestamp string
    """
    milliseconds = round((frame / fps) * 1000)
    totalSeconds = milliseconds // 1000
    ms = milliseconds % 1000
    hours = totalSeconds // 3600
    minutes = (totalSeconds % 3600) // 60
    seconds = totalSeconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"


def processTransnetTimestamps(transnetScenes, fps):
    """
    Convert TransNet scene boundaries to timestamp strings.

    Args:
        transnetScenes: List of (start_frame, end_frame) scene boundaries
        fps: Video frame rate

    Returns:
        str: Formatted timestamp string with one time range per line
    """
    timestampsList = []
    for startFrame, endFrame in transnetScenes:
        startTime = frameToTimestamp(startFrame, fps)
        endTime = frameToTimestamp(endFrame + 1, fps)
        timestampsList.append(f"{startTime}-{endTime}")

    return '\n'.join(timestampsList)


def prepareVideoData(videoId, videoPath, transnetPath, transnetScenes, processor, args):
    """
    Prepare all data for a single video without performing inference.

    Args:
        videoId: Video identifier
        videoPath: Path to video file
        transnetPath: Path to TransNet results file
        transnetScenes: List of TransNet scene boundaries
        processor: Qwen3-VL processor
        args: Configuration arguments

    Returns:
        dict: Prepared video data
    """
    print(f"[prepareVideoData] Preparing {videoId} [time: {datetime.now().strftime('%H:%M:%S')}]")

    with warnings.catch_warnings(), suppressFfmpegLogs():
        warnings.filterwarnings("ignore")
        targetWidth = 640
        targetHeight = 360
        print(f"[prepareVideoData DEBUG] Using fixed resolution: {targetWidth}x{targetHeight}")

        print(f"[prepareVideoData DEBUG] Creating VideoReader...")
        vrCreateStart = time.time()
        vr = decord.VideoReader(
            videoPath,
            width=targetWidth,
            height=targetHeight,
            ctx=decord.cpu(0),
            num_threads=8
        )
        vrCreateTime = time.time() - vrCreateStart
        print(f"[prepareVideoData DEBUG] VideoReader created, took {vrCreateTime:.2f}s")

        totalFrames = len(vr)
        fps = vr.get_avg_fps()
        print(f"[prepareVideoData DEBUG] Video info: {totalFrames} frames, {fps:.2f} fps")

    loadTime = time.time()
    print(f"[prepareVideoData DEBUG] Video loading stage complete, took {loadTime:.2f}s")

    skipStartFrames = int(args.skip_start_seconds * fps)
    skipEndFrames = int(args.skip_end_seconds * fps)

    effectiveStart = min(skipStartFrames, totalFrames)
    effectiveEnd = max(effectiveStart, totalFrames - skipEndFrames)

    if effectiveStart >= effectiveEnd:
        print(f"[WARNING] Video {videoId} too short after trimming: {totalFrames} frames, "
              f"skip {skipStartFrames}+{skipEndFrames} frames")
        effectiveStart = 0
        effectiveEnd = totalFrames

    durationSeconds = totalFrames / fps
    effectiveDuration = (effectiveEnd - effectiveStart) / fps

    if args.no_segment_split:
        segments = [(effectiveStart, effectiveEnd)]
    else:
        maxSegmentFrames = int(args.max_segment_seconds * fps)
        segments = []
        currentStart = effectiveStart
        while currentStart < effectiveEnd:
            currentEnd = min(currentStart + maxSegmentFrames, effectiveEnd)
            segments.append((currentStart, currentEnd))
            currentStart = currentEnd

    segmentData = []
    promptTemplate = loadPromptTemplate(videoPath)
    print(f"[prepareVideoData DEBUG] Preparing {len(segments)} segments...")

    for segIdx, (segStart, segEnd) in enumerate(segments):
        if segIdx % 5 == 0:
            print(f"[prepareVideoData] Processing segment {segIdx+1}/{len(segments)}")
        segDuration = (segEnd - segStart) / fps
        segTotalFrames = segEnd - segStart

        desiredFrames = int(segDuration * args.fps)
        numFrames = max(8, min(args.max_frames_per_segment, desiredFrames))
        numFrames = min(numFrames, segTotalFrames)

        if numFrames < segTotalFrames:
            sampleIndices = np.linspace(0, segTotalFrames - 1, numFrames, dtype=int)
            frameIndices = [segStart + idx for idx in sampleIndices]
        else:
            frameIndices = list(range(segStart, segEnd))

        sampledFrames = vr.get_batch(frameIndices).asnumpy()

        segmentScenes = []
        if transnetScenes:
            for startFrame, endFrame in transnetScenes:
                if startFrame < segEnd and endFrame >= segStart:
                    adjStart = max(startFrame, segStart)
                    adjEnd = min(endFrame, segEnd - 1)
                    relStart = adjStart - segStart
                    relEnd = adjEnd - segStart
                    segmentScenes.append((relStart, relEnd))

        timestamps = ""
        if segmentScenes:
            timestamps = processTransnetTimestamps(segmentScenes, fps)

        systemPrompt = promptTemplate.format("", timestamps)

        videoTensor = torch.from_numpy(sampledFrames).permute(0, 3, 1, 2)
        videoMetadata = {'fps': args.fps, 'frames_indices': list(range(len(sampledFrames))),
                         'total_num_frames': len(sampledFrames)}
        videoInputs = [(videoTensor, videoMetadata)]

        conversation = {
            "role": "user",
            "content": [
                {"type": "video", "video": videoPath, "max_pixels": targetWidth * targetHeight, "fps": args.fps},
                {"type": "text", "text": systemPrompt},
            ],
        }

        userInput = processor.apply_chat_template([conversation], tokenize=False, add_generation_prompt=True)

        inputs = {'prompt': userInput, 'multi_modal_data': {'video': videoInputs},
                 'mm_processor_kwargs': {'do_sample_frames': False}}

        segmentData.append({
            'inputs': inputs,
            'segment_info': {
                'start_frame': segStart,
                'end_frame': segEnd,
                'start_time': frameToTimestamp(segStart, fps),
                'end_time': frameToTimestamp(segEnd, fps),
                'duration': segDuration,
                'num_frames_sampled': len(sampledFrames),
            }
        })

    del vr

    print(f"[prepareVideoData] {videoId} preparation complete, returning {len(segmentData)} segments [time: {datetime.now().strftime('%H:%M:%S')}]")

    return {
        'video_id': videoId,
        'video_path': videoPath,
        'transnet_path': transnetPath,
        'segments': segmentData,
        'video_meta': {'total_frames': totalFrames, 'fps': fps, 'duration_seconds': durationSeconds}
    }


def prepareVideoDataWrapper(argsTuple):
    """
    Multiprocessing wrapper for prepareVideoData.

    Must be top-level function to be pickleable.

    Note: Does not pass processor object (cannot be pickled), reloads in worker.
    """
    videoId, videoPath, transnetPath, transnetScenes, modelPath, args = argsTuple
    try:
        from transformers import AutoProcessor
        processor = AutoProcessor.from_pretrained(modelPath, local_files_only=True)

        return prepareVideoData(videoId, videoPath, transnetPath, transnetScenes, processor, args)
    except Exception as e:
        print(f"[prepareVideoDataWrapper] Error processing {videoId}: {e}")
        import traceback
        traceback.print_exc()
        return None


# Snake_case aliases for backward compatibility
suppress_ffmpeg_logs = suppressFfmpegLogs
load_prompt_template = loadPromptTemplate
frame_to_timestamp = frameToTimestamp
process_transnet_timestamps = processTransnetTimestamps
prepare_video_data = prepareVideoData
prepare_video_data_wrapper = prepareVideoDataWrapper
