"""
Core video quality validation functionality.
Following naming conventions: PascalCase for classes, camelCase for functions/variables.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import cv2
import ffmpeg

from .models import (
    ValidationStatus,
    OperationType,
    OperationStatus,
    VideoValidationResult,
    BatchValidationReport,
    ValidationLog,
)
from .utils import (
    setupLogging,
    generateLogId,
    generateReportId,
    isVideoFile,
)


class VideoQualityValidator:
    """
    Main class for video quality validation.

    Methods:
        __init__(log_dir: str = "./logs")
        validate_single(video_path: str, skip_audio: bool = False) -> VideoValidationResult
        validate_batch(directory_path: str, recursive: bool = False,
                      extensions: List[str] = None, skip_audio: bool = False,
                      parallel: int = 1) -> BatchValidationReport
    """

    def __init__(self, logDir: str = "./logs"):
        """
        Initialize the video quality validator.

        Args:
            logDir: Directory to store log files
        """
        self.logDir = logDir
        self.logger = setupLogging(logDir)

    def _logOperation(self, operation: OperationType, status: OperationStatus,
                      filePath: Optional[str] = None, directoryPath: Optional[str] = None,
                      message: Optional[str] = None, durationMs: Optional[int] = None) -> ValidationLog:
        """
        Log an operation (follows constitution Principle II).

        Args:
            operation: Type of operation
            status: Operation status
            filePath: Related file path (for single file validation)
            directoryPath: Related directory path (for batch validation)
            message: Optional message
            durationMs: Optional duration in milliseconds

        Returns:
            ValidationLog entry
        """
        logEntry = ValidationLog(
            logId=generateLogId(),
            timestamp=datetime.now(),
            operation=operation,
            status=status,
            filePath=filePath,
            directoryPath=directoryPath,
            message=message,
            durationMs=durationMs,
        )

        logMsg = f"{operation.value} - {status.value}"
        if filePath:
            logMsg += f" - File: {filePath}"
        if directoryPath:
            logMsg += f" - Directory: {directoryPath}"
        if message:
            logMsg += f" - {message}"

        if status == OperationStatus.ERROR:
            self.logger.error(logMsg)
        else:
            self.logger.info(logMsg)

        return logEntry

    def validateSingle(self, videoPath: str, skipAudio: bool = False) -> VideoValidationResult:
        """
        Validate a single video file.

        Args:
            videoPath: Path to video file
            skipAudio: Skip audio validation even if audio track exists

        Returns:
            VideoValidationResult with validation details
        """
        startTime = datetime.now()
        absPath = os.path.abspath(videoPath)

        self._logOperation(
            OperationType.VALIDATE_SINGLE,
            OperationStatus.STARTED,
            filePath=absPath,
        )

        result = VideoValidationResult(
            filePath=absPath,
            timestamp=startTime,
            status=ValidationStatus.FAIL,
        )

        try:
            # Check if file exists
            if not os.path.exists(absPath):
                result.decodeError = f"File not found: {absPath}"
                result.validationErrors.append(result.decodeError)
                self._logOperation(
                    OperationType.VALIDATE_SINGLE,
                    OperationStatus.ERROR,
                    filePath=absPath,
                    message=result.decodeError,
                )
                return result

            # Validate video decode integrity and get basic properties (Principle III)
            cap = cv2.VideoCapture(absPath)

            if not cap.isOpened():
                result.decodeError = "Failed to open video file"
                result.validationErrors.append(result.decodeError)
                self._logOperation(
                    OperationType.VALIDATE_SINGLE,
                    OperationStatus.ERROR,
                    filePath=absPath,
                    message=result.decodeError,
                )
                return result

            result.decodeIntegrityPass = True

            # Get frame rate
            result.frameRate = cap.get(cv2.CAP_PROP_FPS)
            result.frameRatePass = result.frameRate > 0

            # Get total frames
            result.totalFrames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            result.totalFramesPass = result.totalFrames > 0

            # Try to read first frame to verify decoding
            ret, _ = cap.read()
            if not ret:
                result.decodeIntegrityPass = False
                result.decodeError = "Failed to read first frame"
                result.validationErrors.append(result.decodeError)

            cap.release()

            # Check for audio using FFmpeg
            if not skipAudio:
                try:
                    probe = ffmpeg.probe(absPath)
                    audioStreams = [s for s in probe["streams"] if s["codec_type"] == "audio"]

                    if audioStreams:
                        result.hasAudio = True
                        audioStream = audioStreams[0]

                        # Get audio sample rate
                        result.audioSampleRate = int(audioStream.get("sample_rate", 0))
                        result.audioSampleRatePass = result.audioSampleRate > 0

                        # Get audio channels
                        result.audioChannels = int(audioStream.get("channels", 0))
                        result.audioChannelsPass = result.audioChannels > 0

                        # Get durations
                        videoDuration = float(probe["format"].get("duration", 0))
                        result.videoDuration = videoDuration if videoDuration > 0 else None

                        # Get audio duration
                        if "duration" in audioStream:
                            audioDuration = float(audioStream["duration"])
                            result.audioDuration = audioDuration if audioDuration > 0 else None
                        else:
                            result.audioDuration = result.videoDuration

                        # Check A/V sync
                        if result.videoDuration and result.audioDuration:
                            durationDiff = abs(result.videoDuration - result.audioDuration)
                            result.avSyncPass = durationDiff <= 1.0  # Allow 1 second difference
                            if not result.avSyncPass:
                                result.validationErrors.append(
                                    f"Audio/video duration mismatch: {durationDiff:.2f}s"
                                )

                except ffmpeg.Error:
                    # Audio check failed, but video may still be valid
                    result.hasAudio = False
                    result.validationErrors.append("Could not probe audio tracks")

            # Determine overall status
            allVideoPass = result.decodeIntegrityPass and result.frameRatePass and result.totalFramesPass

            if result.hasAudio and not skipAudio:
                allAudioPass = (result.audioSampleRatePass and
                               result.audioChannelsPass and
                               result.avSyncPass)

                if allVideoPass and allAudioPass:
                    result.status = ValidationStatus.PASS
                elif allVideoPass:
                    result.status = ValidationStatus.PARTIAL
                else:
                    result.status = ValidationStatus.FAIL
            else:
                result.status = ValidationStatus.PASS if allVideoPass else ValidationStatus.FAIL

            durationMs = int((datetime.now() - startTime).total_seconds() * 1000)

            self._logOperation(
                OperationType.VALIDATE_SINGLE,
                OperationStatus.COMPLETED,
                filePath=absPath,
                message=f"Status: {result.status.value}",
                durationMs=durationMs,
            )

        except Exception as e:
            result.decodeError = str(e)
            result.validationErrors.append(str(e))
            self._logOperation(
                OperationType.VALIDATE_SINGLE,
                OperationStatus.ERROR,
                filePath=absPath,
                message=str(e),
            )

        return result

    def validateBatch(self, directoryPath: str, recursive: bool = False,
                     extensions: Optional[List[str]] = None, skipAudio: bool = False,
                     parallel: int = 1) -> BatchValidationReport:
        """
        Batch validate video files in a directory.

        Args:
            directoryPath: Path to directory containing video files
            recursive: Search recursively in subdirectories
            extensions: List of video extensions to process
            skipAudio: Skip audio validation
            parallel: Number of parallel tasks (currently sequential only)

        Returns:
            BatchValidationReport with summary statistics
        """
        startTime = datetime.now()
        absDirPath = os.path.abspath(directoryPath)

        self._logOperation(
            OperationType.VALIDATE_BATCH,
            OperationStatus.STARTED,
            directoryPath=absDirPath,
        )

        reportId = generateReportId()
        results: List[VideoValidationResult] = []

        # Find all video files
        videoFiles = []
        if recursive:
            for root, _, files in os.walk(absDirPath):
                for file in files:
                    filePath = os.path.join(root, file)
                    if isVideoFile(filePath, extensions):
                        videoFiles.append(filePath)
        else:
            for file in os.listdir(absDirPath):
                filePath = os.path.join(absDirPath, file)
                if os.path.isfile(filePath) and isVideoFile(filePath, extensions):
                    videoFiles.append(filePath)

        # Validate each file
        for videoFile in videoFiles:
            result = self.validateSingle(videoFile, skipAudio)
            results.append(result)

        # Calculate statistics
        totalFiles = len(results)
        passedFiles = sum(1 for r in results if r.status == ValidationStatus.PASS)
        failedFiles = sum(1 for r in results if r.status == ValidationStatus.FAIL)
        partialFiles = sum(1 for r in results if r.status == ValidationStatus.PARTIAL)

        # Build failure summary
        failureSummary = {
            "decodeErrors": 0,
            "frameRateErrors": 0,
            "audioErrors": 0,
            "avSyncErrors": 0,
            "otherErrors": 0,
        }

        for result in results:
            if not result.decodeIntegrityPass:
                failureSummary["decodeErrors"] += 1
            if result.frameRatePass is False:
                failureSummary["frameRateErrors"] += 1
            if result.hasAudio:
                if (result.audioSampleRatePass is False or
                    result.audioChannelsPass is False):
                    failureSummary["audioErrors"] += 1
                if result.avSyncPass is False:
                    failureSummary["avSyncErrors"] += 1

        endTime = datetime.now()

        report = BatchValidationReport(
            reportId=reportId,
            startTime=startTime,
            endTime=endTime,
            totalFiles=totalFiles,
            passedFiles=passedFiles,
            failedFiles=failedFiles,
            partialFiles=partialFiles,
            results=results,
            failureSummary=failureSummary,
        )

        durationMs = int((endTime - startTime).total_seconds() * 1000)

        self._logOperation(
            OperationType.VALIDATE_BATCH,
            OperationStatus.COMPLETED,
            directoryPath=absDirPath,
            message=f"Processed {totalFiles} files, {passedFiles} passed",
            durationMs=durationMs,
        )

        return report


# Aliases for backward compatibility (camelCase)
VideoQualityValidator.validate_single = VideoQualityValidator.validateSingle
VideoQualityValidator.validate_batch = VideoQualityValidator.validateBatch
