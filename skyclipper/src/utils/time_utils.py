#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Time conversion utilities for video processing.

This module provides functions for converting between time strings,
seconds, and frame numbers.
"""

import re


def timeToSeconds(timeStr):
    """
    Convert time string to seconds.

    Supports formats: HH:MM:SS.mmm or HH:MM:SS,mmm

    Args:
        timeStr: Time string in format "HH:MM:SS.mmm" or "HH:MM:SS,mmm"

    Returns:
        float: Total seconds
    """
    timeStr = timeStr.replace(',', '.')
    parts = timeStr.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def secondsToTime(seconds):
    """
    Convert seconds to time string.

    Args:
        seconds: Total seconds (float or int)

    Returns:
        str: Time string in format "HH:MM:SS.mmm"
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def frameToSeconds(frame, fps):
    """
    Convert frame number to seconds.

    Args:
        frame: Frame number (int)
        fps: Frames per second (float)

    Returns:
        float: Time in seconds
    """
    return frame / fps


def secondsToFrame(seconds, fps):
    """
    Convert seconds to frame number.

    Args:
        seconds: Time in seconds (float)
        fps: Frames per second (float)

    Returns:
        int: Frame number
    """
    return int(seconds * fps)


def parseTimeRange(timeRangeStr):
    """
    Parse a time range string into start and end seconds.

    Args:
        timeRangeStr: Time range string like "HH:MM:SS.mmm-HH:MM:SS.mmm"

    Returns:
        tuple: (startSeconds, endSeconds) or (None, None) if invalid
    """
    if '-' not in timeRangeStr:
        return None, None

    startStr, endStr = timeRangeStr.split('-', 1)
    try:
        startSeconds = timeToSeconds(startStr.strip())
        endSeconds = timeToSeconds(endStr.strip())
        return startSeconds, endSeconds
    except (ValueError, IndexError):
        return None, None


def validateTimeFormat(timeStr):
    """
    Validate that a time string is in the correct format.

    Args:
        timeStr: Time string to validate

    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^\d{2}:\d{2}:\d{2}[.,]\d{3}$'
    if not re.match(pattern, timeStr):
        return False
    try:
        timeToSeconds(timeStr)
        return True
    except (ValueError, IndexError):
        return False


# Snake_case aliases for backward compatibility
time_to_seconds = timeToSeconds
seconds_to_time = secondsToTime
frame_to_seconds = frameToSeconds
seconds_to_frame = secondsToFrame
parse_time_range = parseTimeRange
validate_time_format = validateTimeFormat
