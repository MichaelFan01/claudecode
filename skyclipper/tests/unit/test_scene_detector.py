#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for scene_detector module.

Note: Full testing requires TransNetV2 and video files, which may not be available.
These tests focus on the non-hardware-dependent functionality.
"""

import pytest
import tempfile
import os
from src.core.scene_detector import (
    TransNetWorker,
    suppressFfmpegLogs,
    suppress_ffmpeg_logs,
    TRANSNET_AVAILABLE,
)


class TestSuppressFfmpegLogs:
    """Tests for suppressFfmpegLogs context manager."""

    def test_context_manager_exists(self):
        """Test that the context manager exists and can be used."""
        # Just test that it doesn't crash when used
        with suppressFfmpegLogs():
            pass
        assert True

    def test_snake_case_alias(self):
        """Test that the snake_case alias exists."""
        assert suppress_ffmpeg_logs is suppressFfmpegLogs


class TestTransNetWorker:
    """Tests for TransNetWorker class."""

    def test_worker_initialization_without_transnet(self):
        """Test worker initialization behavior when TransNet is not available."""
        if not TRANSNET_AVAILABLE:
            # If TransNet is not available, initialization should fail gracefully
            worker = TransNetWorker(0, "/nonexistent/path.pth")
            result = worker.initialize()
            assert result is False
        else:
            # Skip if TransNet is available - would need actual weights
            pytest.skip("TransNet available, skipping initialization test")

    def test_process_video_nonexistent_file(self):
        """Test processing a nonexistent video file."""
        worker = TransNetWorker(0, "/nonexistent/path.pth")
        # Set model to None to simulate uninitialized state
        worker.model = None

        # Process nonexistent file
        scenes = worker.processVideo("/nonexistent/video.mp4")
        assert scenes == []

    def test_worker_attributes(self):
        """Test that worker attributes are set correctly."""
        worker = TransNetWorker(
            workerId=5,
            weightsPath="/test/path.pth",
            threshold=0.5,
            device='cpu'
        )

        assert worker.workerId == 5
        assert worker.weightsPath == "/test/path.pth"
        assert worker.threshold == 0.5
        assert worker.device == 'cpu'
        assert worker.model is None


class TestTransNetAvailability:
    """Tests related to TransNet availability."""

    def test_transnet_available_flag(self):
        """Test that TRANSNET_AVAILABLE is defined."""
        assert isinstance(TRANSNET_AVAILABLE, bool)
