#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for time_utils module.
"""

import pytest
from src.utils.time_utils import (
    timeToSeconds,
    secondsToTime,
    frameToSeconds,
    secondsToFrame,
    parseTimeRange,
    validateTimeFormat,
    time_to_seconds,
    seconds_to_time,
    frame_to_seconds,
    seconds_to_frame,
    parse_time_range,
    validate_time_format,
)


class TestTimeToSeconds:
    """Tests for timeToSeconds function."""

    def test_basic_conversion(self):
        """Test basic time string to seconds conversion."""
        assert timeToSeconds("00:00:00.000") == 0.0
        assert timeToSeconds("00:00:01.000") == 1.0
        assert timeToSeconds("00:01:00.000") == 60.0
        assert timeToSeconds("01:00:00.000") == 3600.0

    def test_with_milliseconds(self):
        """Test conversion with millisecond precision."""
        assert timeToSeconds("00:00:00.500") == 0.5
        assert timeToSeconds("00:00:01.250") == 1.25
        assert timeToSeconds("00:01:30.750") == 90.75

    def test_comma_decimal_separator(self):
        """Test that comma decimal separator is handled correctly."""
        assert timeToSeconds("00:00:00,500") == 0.5
        assert timeToSeconds("00:00:01,250") == 1.25


class TestSecondsToTime:
    """Tests for secondsToTime function."""

    def test_basic_conversion(self):
        """Test basic seconds to time string conversion."""
        assert secondsToTime(0.0) == "00:00:00.000"
        assert secondsToTime(1.0) == "00:00:01.000"
        assert secondsToTime(60.0) == "00:01:00.000"
        assert secondsToTime(3600.0) == "01:00:00.000"

    def test_with_milliseconds(self):
        """Test conversion with millisecond precision."""
        assert secondsToTime(0.5) == "00:00:00.500"
        assert secondsToTime(1.25) == "00:00:01.250"
        assert secondsToTime(90.75) == "00:01:30.750"

    def test_large_values(self):
        """Test with large second values."""
        assert secondsToTime(3661.5) == "01:01:01.500"
        assert secondsToTime(7200.0) == "02:00:00.000"


class TestFrameConversions:
    """Tests for frameToSeconds and secondsToFrame functions."""

    def test_frame_to_seconds(self):
        """Test frame number to seconds conversion."""
        assert frameToSeconds(0, 30.0) == 0.0
        assert frameToSeconds(30, 30.0) == 1.0
        assert frameToSeconds(45, 30.0) == 1.5
        assert frameToSeconds(60, 24.0) == 2.5

    def test_seconds_to_frame(self):
        """Test seconds to frame number conversion."""
        assert secondsToFrame(0.0, 30.0) == 0
        assert secondsToFrame(1.0, 30.0) == 30
        assert secondsToFrame(1.5, 30.0) == 45
        assert secondsToFrame(2.5, 24.0) == 60


class TestParseTimeRange:
    """Tests for parseTimeRange function."""

    def test_valid_range(self):
        """Test parsing a valid time range."""
        start, end = parseTimeRange("00:00:00.000-00:00:10.000")
        assert start == 0.0
        assert end == 10.0

    def test_range_with_spaces(self):
        """Test parsing with spaces around the separator."""
        start, end = parseTimeRange("00:00:00.000 - 00:00:10.000")
        assert start == 0.0
        assert end == 10.0

    def test_invalid_range(self):
        """Test parsing invalid time ranges."""
        start, end = parseTimeRange("not a range")
        assert start is None
        assert end is None


class TestValidateTimeFormat:
    """Tests for validateTimeFormat function."""

    def test_valid_formats(self):
        """Test valid time formats."""
        assert validateTimeFormat("00:00:00.000") is True
        assert validateTimeFormat("01:23:45.678") is True
        assert validateTimeFormat("00:00:00,000") is True

    def test_invalid_formats(self):
        """Test invalid time formats."""
        assert validateTimeFormat("0:00:00.000") is False  # Too few digits
        assert validateTimeFormat("00:00.000") is False   # Missing hour
        assert validateTimeFormat("not a time") is False
        assert validateTimeFormat("") is False


class TestSnakeCaseAliases:
    """Tests for snake_case alias functions."""

    def test_aliases_exist_and_work(self):
        """Test that snake_case aliases exist and work correctly."""
        assert time_to_seconds("00:00:01.000") == 1.0
        assert seconds_to_time(1.0) == "00:00:01.000"
        assert frame_to_seconds(30, 30.0) == 1.0
        assert seconds_to_frame(1.0, 30.0) == 30

        start, end = parse_time_range("00:00:00.000-00:00:10.000")
        assert start == 0.0
        assert end == 10.0

        assert validate_time_format("00:00:00.000") is True
