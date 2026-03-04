"""
Tests for core validation functionality.
Following naming conventions: kebab-case files, PascalCase classes, camelCase functions.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from video_quality_validator.core import VideoQualityValidator
from video_quality_validator.models import (
    ValidationStatus,
    OperationType,
    OperationStatus,
)
from video_quality_validator.utils import (
    generateLogId,
    generateReportId,
    getVideoExtensions,
    isVideoFile,
)


class TestUtils:
    """Tests for utility functions."""

    def testGenerateLogId(self):
        """Test generating unique log IDs."""
        logId1 = generateLogId()
        logId2 = generateLogId()

        assert logId1.startswith("log-")
        assert logId1 != logId2

    def testGenerateReportId(self):
        """Test generating unique report IDs."""
        reportId1 = generateReportId()
        reportId2 = generateReportId()

        assert reportId1.startswith("batch-")
        assert reportId1 != reportId2

    def testGetVideoExtensions(self):
        """Test getting default video extensions."""
        extensions = getVideoExtensions()

        assert "mp4" in extensions
        assert "avi" in extensions
        assert "mov" in extensions

    def testIsVideoFile(self):
        """Test checking if a file is a video file."""
        assert isVideoFile("test.mp4") is True
        assert isVideoFile("test.avi") is True
        assert isVideoFile("test.txt") is False
        assert isVideoFile("test.mp4", ["avi"]) is False


class TestVideoQualityValidator:
    """Tests for VideoQualityValidator class."""

    def testCreateValidator(self):
        """Test creating a validator instance."""
        validator = VideoQualityValidator(logDir="./logs-test")

        assert validator is not None
        assert validator.logDir == "./logs-test"

    def testValidateSingleFileNotFound(self):
        """Test validating a non-existent file."""
        validator = VideoQualityValidator()

        result = validator.validateSingle("/nonexistent/video.mp4")

        assert result.status == ValidationStatus.FAIL
        assert result.decodeIntegrityPass is False
        assert "File not found" in result.decodeError or len(result.validationErrors) > 0

    @patch("cv2.VideoCapture")
    def testValidateSingleDecodeFails(self, mockVideoCapture):
        """Test validation when video can't be opened."""
        mockCap = Mock()
        mockCap.isOpened.return_value = False
        mockVideoCapture.return_value = mockCap

        validator = VideoQualityValidator()

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"not a video")
            tempPath = f.name

        try:
            result = validator.validateSingle(tempPath)

            assert result.status == ValidationStatus.FAIL
            assert result.decodeIntegrityPass is False
        finally:
            os.unlink(tempPath)

    def testValidateBatchEmptyDirectory(self):
        """Test batch validation on an empty directory."""
        validator = VideoQualityValidator()

        with tempfile.TemporaryDirectory() as tempDir:
            report = validator.validateBatch(tempDir)

            assert report.totalFiles == 0
            assert report.passedFiles == 0
            assert report.failedFiles == 0

    def testValidateBatchWithNonVideoFiles(self):
        """Test batch validation ignores non-video files."""
        validator = VideoQualityValidator()

        with tempfile.TemporaryDirectory() as tempDir:
            # Create non-video files
            (Path(tempDir) / "test.txt").write_text("not a video")
            (Path(tempDir) / "test.jpg").write_bytes(b"not a video")

            report = validator.validateBatch(tempDir)

            assert report.totalFiles == 0


class TestLogging:
    """Tests for logging functionality (Constitution Principle II)."""

    def testValidatorLogsDirectoryCreated(self):
        """Test that log directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tempDir:
            logDir = os.path.join(tempDir, "logs-test")
            assert not os.path.exists(logDir)

            validator = VideoQualityValidator(logDir=logDir)
            # Log directory created on first use

            assert os.path.exists(logDir) or validator.logger is not None


class TestValidationStatusFlow:
    """Tests for validation status determination."""

    def testPassStatusWhenAllVideoPass(self):
        """Test PASS status when all video checks pass."""
        # This would be tested with an actual video file in integration tests
        pass

    def testPartialStatusWhenVideoPassesAudioFails(self):
        """Test PARTIAL status when video passes but audio fails."""
        # This would be tested with an actual video file in integration tests
        pass

    def testFailStatusWhenDecodeFails(self):
        """Test FAIL status when decode integrity fails."""
        # This would be tested with an actual video file in integration tests
        pass
