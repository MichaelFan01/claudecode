"""
Tests for data models.
Following naming conventions: kebab-case files, PascalCase classes, camelCase functions.
"""

import pytest
from datetime import datetime

from video_quality_validator.models import (
    ValidationStatus,
    OperationType,
    OperationStatus,
    VideoValidationResult,
    BatchValidationReport,
    ValidationLog,
)


class TestValidationStatus:
    """Tests for ValidationStatus enum."""

    def testValidationStatusValues(self):
        """Test that ValidationStatus has correct values."""
        assert ValidationStatus.PASS.value == "PASS"
        assert ValidationStatus.FAIL.value == "FAIL"
        assert ValidationStatus.PARTIAL.value == "PARTIAL"


class TestVideoValidationResult:
    """Tests for VideoValidationResult model."""

    def testCreateBasicResult(self):
        """Test creating a basic validation result."""
        result = VideoValidationResult(
            filePath="/test/video.mp4",
            timestamp=datetime.now(),
            status=ValidationStatus.PASS,
        )

        assert result.filePath == "/test/video.mp4"
        assert result.status == ValidationStatus.PASS
        assert result.decodeIntegrityPass is False
        assert result.hasAudio is False

    def testResultWithVideoProperties(self):
        """Test creating a result with video properties."""
        result = VideoValidationResult(
            filePath="/test/video.mp4",
            timestamp=datetime.now(),
            status=ValidationStatus.PASS,
            frameRate=30.0,
            frameRatePass=True,
            totalFrames=1800,
            totalFramesPass=True,
            decodeIntegrityPass=True,
        )

        assert result.frameRate == 30.0
        assert result.frameRatePass is True
        assert result.totalFrames == 1800
        assert result.totalFramesPass is True

    def testResultWithAudio(self):
        """Test creating a result with audio properties."""
        result = VideoValidationResult(
            filePath="/test/video.mp4",
            timestamp=datetime.now(),
            status=ValidationStatus.PASS,
            hasAudio=True,
            audioSampleRate=44100,
            audioSampleRatePass=True,
            audioChannels=2,
            audioChannelsPass=True,
            videoDuration=60.0,
            audioDuration=60.0,
            avSyncPass=True,
        )

        assert result.hasAudio is True
        assert result.audioSampleRate == 44100
        assert result.audioChannels == 2
        assert result.avSyncPass is True

    def testResultToDict(self):
        """Test converting result to dictionary."""
        result = VideoValidationResult(
            filePath="/test/video.mp4",
            timestamp=datetime.now(),
            status=ValidationStatus.PASS,
            decodeIntegrityPass=True,
        )

        d = result.to_dict()

        assert d["filePath"] == "/test/video.mp4"
        assert d["status"] == "PASS"
        assert "timestamp" in d


class TestBatchValidationReport:
    """Tests for BatchValidationReport model."""

    def testCreateBasicReport(self):
        """Test creating a basic batch report."""
        startTime = datetime.now()
        endTime = datetime.now()

        report = BatchValidationReport(
            reportId="batch-001",
            startTime=startTime,
            endTime=endTime,
            totalFiles=10,
            passedFiles=8,
            failedFiles=1,
            partialFiles=1,
            results=[],
        )

        assert report.reportId == "batch-001"
        assert report.totalFiles == 10
        assert report.passedFiles == 8
        assert report.failedFiles == 1
        assert report.partialFiles == 1

    def testReportToDict(self):
        """Test converting report to dictionary."""
        startTime = datetime.now()
        endTime = datetime.now()

        report = BatchValidationReport(
            reportId="batch-001",
            startTime=startTime,
            endTime=endTime,
            totalFiles=10,
            passedFiles=8,
            failedFiles=1,
            partialFiles=1,
            results=[],
        )

        d = report.to_dict()

        assert d["reportId"] == "batch-001"
        assert d["totalFiles"] == 10
        assert "startTime" in d
        assert "endTime" in d


class TestValidationLog:
    """Tests for ValidationLog model."""

    def testCreateBasicLog(self):
        """Test creating a basic validation log."""
        log = ValidationLog(
            logId="log-001",
            timestamp=datetime.now(),
            operation=OperationType.VALIDATE_SINGLE,
            status=OperationStatus.COMPLETED,
        )

        assert log.logId == "log-001"
        assert log.operation == OperationType.VALIDATE_SINGLE
        assert log.status == OperationStatus.COMPLETED

    def testLogWithFilePath(self):
        """Test creating a log with file path."""
        log = ValidationLog(
            logId="log-001",
            timestamp=datetime.now(),
            operation=OperationType.VALIDATE_SINGLE,
            status=OperationStatus.COMPLETED,
            filePath="/test/video.mp4",
        )

        assert log.filePath == "/test/video.mp4"

    def testLogToDict(self):
        """Test converting log to dictionary."""
        log = ValidationLog(
            logId="log-001",
            timestamp=datetime.now(),
            operation=OperationType.VALIDATE_SINGLE,
            status=OperationStatus.COMPLETED,
        )

        d = log.to_dict()

        assert d["logId"] == "log-001"
        assert d["operation"] == "VALIDATE_SINGLE"
        assert d["status"] == "COMPLETED"
