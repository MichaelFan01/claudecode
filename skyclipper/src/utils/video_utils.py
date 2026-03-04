#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video processing utilities.

This module provides helper functions for video-related operations
including FPS calculation, duration calculation, and metadata handling.
"""

import os
from .time_utils import timeToSeconds


# TransNet boundary cache (process-level cache)
_transnetCache = {}


def getVideoFpsFromClips(clips, videoMeta=None):
    """
    Calculate video FPS from clips or video metadata.

    First tries to get FPS from video_meta, then tries to calculate from
    clips' frame numbers and timestamps, falls back to default 30.0.

    Args:
        clips: List of clip dictionaries with frame fields
        videoMeta: Optional video metadata dict with 'fps' key

    Returns:
        float: Video frames per second, default 30.0
    """
    # First try from video_meta
    if videoMeta and 'fps' in videoMeta:
        fps = videoMeta.get('fps')
        if fps and 15 < fps < 120:
            return fps

    # Try to calculate from clips
    for clip in clips:
        startFrame = clip.get('start_frame', 0)
        endFrame = clip.get('end_frame', 0)

        if startFrame > 0 and endFrame > startFrame:
            try:
                startTime = timeToSeconds(clip['start_time'])
                endTime = timeToSeconds(clip['end_time'])
                duration = endTime - startTime
                frameCount = endFrame - startFrame

                if duration > 0:
                    fps = frameCount / duration
                    if 15 < fps < 120:  # Reasonable range
                        return fps
            except (ValueError, IndexError, KeyError):
                continue

    # Default 30fps (common video frame rate)
    return 30.0


def calculateClipDuration(clip):
    """
    Calculate duration of a single clip in seconds.

    Args:
        clip: Clip dictionary with 'start_time' and 'end_time'

    Returns:
        float: Duration in seconds, or 0.0 on error
    """
    try:
        startSeconds = timeToSeconds(clip['start_time'])
        endSeconds = timeToSeconds(clip['end_time'])
        return endSeconds - startSeconds
    except (KeyError, ValueError, IndexError):
        return 0.0


def calculateTotalDuration(clips):
    """
    Calculate total duration of all clips.

    Args:
        clips: List of clip dictionaries

    Returns:
        float: Total duration in seconds
    """
    total = 0.0
    for clip in clips:
        total += calculateClipDuration(clip)
    return total


def readTransnetBoundaries(transnetPath, videoFps):
    """
    Read TransNet scene boundary timestamps with caching.

    Args:
        transnetPath: Path to TransNet result file
        videoFps: Video frame rate

    Returns:
        list: Boundary timestamps in seconds (sorted, deduplicated)
    """
    if not transnetPath:
        return []

    if not os.path.exists(transnetPath):
        return []

    # Use cache
    cacheKey = (transnetPath, videoFps)
    if cacheKey in _transnetCache:
        return _transnetCache[cacheKey]

    boundaries = []
    try:
        with open(transnetPath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split()
                if len(parts) >= 2:
                    startFrame = int(parts[0])
                    endFrame = int(parts[1])

                    # Both start and end times are boundary points
                    from .time_utils import frameToSeconds
                    startTime = frameToSeconds(startFrame, videoFps)
                    endTime = frameToSeconds(endFrame + 1, videoFps)  # +1 ensures continuity

                    boundaries.append(startTime)
                    boundaries.append(endTime)

        # Deduplicate and sort
        boundaries = sorted(list(set(boundaries)))

    except Exception:
        pass  # Silent failure, no error printing

    # Cache result
    _transnetCache[cacheKey] = boundaries
    return boundaries


def clearTransnetCache():
    """Clear the TransNet boundary cache."""
    global _transnetCache
    _transnetCache = {}


def ensureClipFrames(clip, videoFps):
    """
    Ensure clip has start_frame and end_frame fields.

    Calculates frame numbers from time strings if missing.

    Args:
        clip: Clip dictionary
        videoFps: Video frame rate

    Returns:
        dict: Clip with frame fields (modified in-place)
    """
    from .time_utils import timeToSeconds, secondsToFrame

    if 'start_frame' not in clip or clip.get('start_frame', 0) == 0:
        try:
            startSeconds = timeToSeconds(clip['start_time'])
            clip['start_frame'] = secondsToFrame(startSeconds, videoFps)
        except (KeyError, ValueError, IndexError):
            clip['start_frame'] = 0

    if 'end_frame' not in clip or clip.get('end_frame', 0) == 0:
        try:
            endSeconds = timeToSeconds(clip['end_time'])
            clip['end_frame'] = secondsToFrame(endSeconds, videoFps)
        except (KeyError, ValueError, IndexError):
            clip['end_frame'] = 0

    return clip


def areClipsAdjacent(clip1, clip2, tolerance=0.5):
    """
    Check if two clips are adjacent in time.

    Args:
        clip1: First clip
        clip2: Second clip
        tolerance: Maximum gap in seconds to consider adjacent

    Returns:
        bool: True if clips are adjacent
    """
    try:
        end1 = timeToSeconds(clip1['end_time'])
        start2 = timeToSeconds(clip2['start_time'])
        return abs(start2 - end1) < tolerance
    except (KeyError, ValueError, IndexError):
        return False


def getClipOverlap(clip1, clip2):
    """
    Calculate overlap between two clips in seconds.

    Args:
        clip1: First clip
        clip2: Second clip

    Returns:
        float: Overlap duration in seconds (0 if no overlap)
    """
    try:
        start1 = timeToSeconds(clip1['start_time'])
        end1 = timeToSeconds(clip1['end_time'])
        start2 = timeToSeconds(clip2['start_time'])
        end2 = timeToSeconds(clip2['end_time'])

        latestStart = max(start1, start2)
        earliestEnd = min(end1, end2)

        return max(0.0, earliestEnd - latestStart)
    except (KeyError, ValueError, IndexError):
        return 0.0


def validateClip(clip):
    """
    Validate that a clip has all required fields and valid times.

    Args:
        clip: Clip dictionary to validate

    Returns:
        tuple: (isValid, errorMessage)
    """
    requiredFields = ['start_time', 'end_time', 'action_id']
    for field in requiredFields:
        if field not in clip:
            return False, f"Missing required field: {field}"

    try:
        start = timeToSeconds(clip['start_time'])
        end = timeToSeconds(clip['end_time'])
        if end <= start:
            return False, "End time must be after start time"
    except (ValueError, IndexError):
        return False, "Invalid time format"

    if not isinstance(clip.get('action_id'), int):
        try:
            clip['action_id'] = int(clip['action_id'])
        except (ValueError, TypeError):
            return False, "action_id must be an integer"

    return True, ""


# Snake_case aliases for backward compatibility
get_video_fps_from_clips = getVideoFpsFromClips
calculate_clip_duration = calculateClipDuration
calculate_total_duration = calculateTotalDuration
read_transnet_boundaries = readTransnetBoundaries
clear_transnet_cache = clearTransnetCache
ensure_clip_frames = ensureClipFrames
are_clips_adjacent = areClipsAdjacent
get_clip_overlap = getClipOverlap
validate_clip = validateClip
