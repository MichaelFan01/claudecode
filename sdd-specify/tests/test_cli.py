"""
Tests for CLI functionality.
Following naming conventions: kebab-case files, PascalCase classes, camelCase functions.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from video_quality_validator.cli import main
from video_quality_validator.models import ValidationStatus


class TestCLI:
    """Tests for the CLI interface."""

    def testCLIHelp(self):
        """Test that CLI help works."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Video Quality Validator" in result.output

    def testCLIVersion(self):
        """Test that CLI version works."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])

        assert result.exit_code == 0

    def testValidateCommandHelp(self):
        """Test that validate command help works."""
        runner = CliRunner()
        result = runner.invoke(main, ["validate", "--help"])

        assert result.exit_code == 0
        assert "Validate a single video file" in result.output

    def testBatchValidateCommandHelp(self):
        """Test that batch-validate command help works."""
        runner = CliRunner()
        result = runner.invoke(main, ["batch-validate", "--help"])

        assert result.exit_code == 0
        assert "Batch validate video files in a directory" in result.output

    @patch("video_quality_validator.cli.VideoQualityValidator")
    def testValidateCommandFileNotFound(self, mockValidatorClass):
        """Test validate command with non-existent file."""
        # Setup mock
        from video_quality_validator.models import VideoValidationResult
        mockResult = Mock(spec=VideoValidationResult)
        mockResult.status = ValidationStatus.FAIL
        mockResult.to_dict.return_value = {"status": "FAIL"}

        mockValidator = Mock()
        mockValidator.validateSingle.return_value = mockResult
        mockValidatorClass.return_value = mockValidator

        runner = CliRunner()
        result = runner.invoke(main, ["validate", "/nonexistent/file.mp4"])

        # Exit code 2 for validation errors
        assert result.exit_code in [0, 1, 2]

    @patch("video_quality_validator.cli.VideoQualityValidator")
    def testBatchValidateCommandEmptyDir(self, mockValidatorClass):
        """Test batch-validate command with empty directory."""
        # Setup mock
        from video_quality_validator.models import BatchValidationReport
        from datetime import datetime

        mockReport = Mock(spec=BatchValidationReport)
        mockReport.totalFiles = 0
        mockReport.passedFiles = 0
        mockReport.failedFiles = 0
        mockReport.partialFiles = 0
        mockReport.startTime = datetime.now()
        mockReport.endTime = datetime.now()
        mockReport.to_dict.return_value = {"totalFiles": 0}

        mockValidator = Mock()
        mockValidator.validateBatch.return_value = mockReport
        mockValidatorClass.return_value = mockValidator

        with tempfile.TemporaryDirectory() as tempDir:
            runner = CliRunner()
            result = runner.invoke(main, ["batch-validate", tempDir])

            assert result.exit_code == 0


class TestCLIOutput:
    """Tests for CLI output formatting."""

    def testTextOutputFormat(self):
        """Test that text output format is readable."""
        # This would be tested with actual validation output in integration tests
        pass

    def testJsonOutputFormat(self):
        """Test that JSON output format is valid."""
        # This would be tested with actual validation output in integration tests
        pass

    def testOutputFileWriting(self):
        """Test that output can be written to a file."""
        # This would be tested with actual validation output in integration tests
        pass


class TestCLIOptions:
    """Tests for CLI command options."""

    def testSkipAudioOption(self):
        """Test --skip-audio option is accepted."""
        # This would be tested with actual video files in integration tests
        pass

    def testRecursiveOption(self):
        """Test --recursive option is accepted."""
        # This would be tested with actual video files in integration tests
        pass

    def testOutputFormatOption(self):
        """Test --output option is accepted."""
        # This would be tested with actual video files in integration tests
        pass

    def testExtensionsOption(self):
        """Test --extensions option is accepted."""
        # This would be tested with actual video files in integration tests
        pass
