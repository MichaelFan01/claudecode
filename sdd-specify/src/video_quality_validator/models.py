"""
Data models for video quality validation.
Following naming conventions: PascalCase for classes, camelCase for functions/variables.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum


class ValidationStatus(Enum):
    """Validation result status."""
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"


class OperationType(Enum):
    """Types of validation operations."""
    VALIDATE_SINGLE = "VALIDATE_SINGLE"
    VALIDATE_BATCH = "VALIDATE_BATCH"
    GENERATE_REPORT = "GENERATE_REPORT"


class OperationStatus(Enum):
    """Status of an operation."""
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


@dataclass
class VideoValidationResult:
    """
    Single video file validation result containing pass/fail status and details.

    Attributes:
        filePath: Absolute path to the video file (required)
        timestamp: Validation execution time (required)
        status: Overall validation status (required)
    """
    filePath: str
    timestamp: datetime
    status: ValidationStatus

    # Video properties
    frameRate: Optional[float] = None
    frameRatePass: Optional[bool] = None
    totalFrames: Optional[int] = None
    totalFramesPass: Optional[bool] = None
    decodeIntegrityPass: bool = False
    decodeError: Optional[str] = None

    # Audio properties
    hasAudio: bool = False
    audioSampleRate: Optional[int] = None
    audioSampleRatePass: Optional[bool] = None
    audioChannels: Optional[int] = None
    audioChannelsPass: Optional[bool] = None
    videoDuration: Optional[float] = None
    audioDuration: Optional[float] = None
    avSyncPass: Optional[bool] = None

    validationErrors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert result to dictionary for JSON serialization."""
        return {
            "filePath": self.filePath,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "frameRate": self.frameRate,
            "frameRatePass": self.frameRatePass,
            "totalFrames": self.totalFrames,
            "totalFramesPass": self.totalFramesPass,
            "decodeIntegrityPass": self.decodeIntegrityPass,
            "decodeError": self.decodeError,
            "hasAudio": self.hasAudio,
            "audioSampleRate": self.audioSampleRate,
            "audioSampleRatePass": self.audioSampleRatePass,
            "audioChannels": self.audioChannels,
            "audioChannelsPass": self.audioChannelsPass,
            "videoDuration": self.videoDuration,
            "audioDuration": self.audioDuration,
            "avSyncPass": self.avSyncPass,
            "validationErrors": self.validationErrors
        }


@dataclass
class BatchValidationReport:
    """
    Batch validation summary report with statistics.

    Attributes:
        reportId: Unique report identifier (required)
        startTime: Batch validation start time (required)
        endTime: Batch validation end time (required)
        totalFiles: Total number of files processed (required)
        passedFiles: Number of files that fully passed (required)
        failedFiles: Number of files that failed validation (required)
        partialFiles: Number of files that partially passed (required)
        results: Detailed results for each file (required)
    """
    reportId: str
    startTime: datetime
    endTime: datetime
    totalFiles: int
    passedFiles: int
    failedFiles: int
    partialFiles: int
    results: List[VideoValidationResult]
    failureSummary: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert report to dictionary for JSON serialization."""
        return {
            "reportId": self.reportId,
            "startTime": self.startTime.isoformat(),
            "endTime": self.endTime.isoformat(),
            "totalFiles": self.totalFiles,
            "passedFiles": self.passedFiles,
            "failedFiles": self.failedFiles,
            "partialFiles": self.partialFiles,
            "results": [r.to_dict() for r in self.results],
            "failureSummary": self.failureSummary
        }


@dataclass
class ValidationLog:
    """
    Log entry for validation operations.

    Attributes:
        logId: Unique log entry identifier (required)
        timestamp: Log recording time (required)
        operation: Type of operation performed (required)
        status: Operation status (required)
    """
    logId: str
    timestamp: datetime
    operation: OperationType
    status: OperationStatus
    filePath: Optional[str] = None
    directoryPath: Optional[str] = None
    message: Optional[str] = None
    durationMs: Optional[int] = None

    def to_dict(self) -> Dict:
        """Convert log entry to dictionary."""
        return {
            "logId": self.logId,
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation.value,
            "status": self.status.value,
            "filePath": self.filePath,
            "directoryPath": self.directoryPath,
            "message": self.message,
            "durationMs": self.durationMs
        }
