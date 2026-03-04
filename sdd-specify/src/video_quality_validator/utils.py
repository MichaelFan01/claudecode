"""
Utility functions for video quality validation.
Following naming conventions: kebab-case for files, camelCase for functions/variables.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def setupLogging(logDir: str = "./logs", verbose: bool = False) -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        logDir: Directory to store log files
        verbose: Enable verbose logging

    Returns:
        Configured logger instance
    """
    # Create log directory if it doesn't exist
    Path(logDir).mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("video_quality_validator")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # File handler - writes to dated log file
    dateStr = datetime.now().strftime("%Y-%m-%d")
    logFile = os.path.join(logDir, f"validation-{dateStr}.log")
    fileHandler = logging.FileHandler(logFile)
    fileHandler.setLevel(logging.DEBUG)

    # Console handler
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fileHandler.setFormatter(formatter)
    consoleHandler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(fileHandler)
    logger.addHandler(consoleHandler)

    return logger


def generateLogId() -> str:
    """
    Generate a unique log ID.

    Returns:
        Unique log ID string
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    return f"log-{timestamp}"


def generateReportId() -> str:
    """
    Generate a unique report ID.

    Returns:
        Unique report ID string
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"batch-{timestamp}"


def getVideoExtensions() -> list:
    """
    Get default list of video file extensions.

    Returns:
        List of video file extensions
    """
    return ["mp4", "avi", "mov", "webm", "mkv"]


def isVideoFile(filePath: str, extensions: Optional[list] = None) -> bool:
    """
    Check if a file is a video file based on extension.

    Args:
        filePath: Path to the file
        extensions: List of valid video extensions (uses default if None)

    Returns:
        True if file is a video file, False otherwise
    """
    if extensions is None:
        extensions = getVideoExtensions()

    ext = Path(filePath).suffix.lower().lstrip(".")
    return ext in extensions
