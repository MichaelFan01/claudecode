"""
Command line interface for video quality validator.
Following naming conventions: kebab-case for commands, camelCase for functions.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .core import VideoQualityValidator
from .models import ValidationStatus
from .utils import getVideoExtensions


def printTextResult(result) -> None:
    """Print validation result in human-readable text format."""
    click.echo("\nVideo Validation Result")
    click.echo("=" * 50)
    click.echo(f"File: {result.filePath}")
    click.echo(f"Status: {_colorizeStatus(result.status.value, result.status)}")
    click.echo(f"Timestamp: {result.timestamp.isoformat()}")

    click.echo("\nVideo Properties:")
    if result.frameRate is not None:
        fps_ok = " ✓" if result.frameRatePass else ""
        click.echo(f"  - Frame Rate: {result.frameRate} FPS{fps_ok}")
    if result.totalFrames is not None:
        frames_ok = " ✓" if result.totalFramesPass else ""
        click.echo(f"  - Total Frames: {result.totalFrames}{frames_ok}")
    decode_ok = " ✓" if result.decodeIntegrityPass else " ✗"
    click.echo(f"  - Decode Integrity: PASS{decode_ok}" if result.decodeIntegrityPass else f"  - Decode Integrity: FAIL{decode_ok}")
    if result.decodeError:
        click.echo(f"    Error: {result.decodeError}")

    if result.hasAudio:
        click.echo("\nAudio Properties:")
        click.echo(f"  - Has Audio: Yes")
        if result.audioSampleRate is not None:
            sr_ok = " ✓" if result.audioSampleRatePass else ""
            click.echo(f"  - Sample Rate: {result.audioSampleRate} Hz{sr_ok}")
        if result.audioChannels is not None:
            ch_ok = " ✓" if result.audioChannelsPass else ""
            click.echo(f"  - Channels: {result.audioChannels}{ch_ok}")
        if result.videoDuration:
            click.echo(f"  - Video Duration: {result.videoDuration:.2f}s")
        if result.audioDuration:
            click.echo(f"  - Audio Duration: {result.audioDuration:.2f}s")
        if result.avSyncPass is not None:
            sync_ok = " ✓" if result.avSyncPass else " ✗"
            click.echo(f"  - A/V Sync: PASS{sync_ok}" if result.avSyncPass else f"  - A/V Sync: FAIL{sync_ok}")
    else:
        click.echo("\nAudio Properties:")
        click.echo(f"  - Has Audio: No")

    if result.validationErrors:
        click.echo("\nValidation Errors:")
        for err in result.validationErrors:
            click.echo(f"  - {err}")


def printTextReport(report) -> None:
    """Print batch validation report in human-readable text format."""
    duration = (report.endTime - report.startTime).total_seconds()

    click.echo("\nBatch Validation Report")
    click.echo("=" * 50)
    click.echo(f"Start Time: {report.startTime.isoformat()}")
    click.echo(f"End Time: {report.endTime.isoformat()}")
    click.echo(f"Duration: {duration:.1f}s")

    click.echo("\nSummary:")
    click.echo(f"  - Total Files: {report.totalFiles}")
    click.echo(f"  - Passed: {_colorizeStatus(str(report.passedFiles), ValidationStatus.PASS)}")
    click.echo(f"  - Failed: {_colorizeStatus(str(report.failedFiles), ValidationStatus.FAIL)}")
    click.echo(f"  - Partial: {_colorizeStatus(str(report.partialFiles), ValidationStatus.PARTIAL)}")
    if report.totalFiles > 0:
        passRate = (report.passedFiles / report.totalFiles) * 100
        click.echo(f"  - Pass Rate: {passRate:.1f}%")

    click.echo("\nFailure Breakdown:")
    click.echo(f"  - Decode Errors: {report.failureSummary.get('decodeErrors', 0)}")
    click.echo(f"  - Frame Rate Errors: {report.failureSummary.get('frameRateErrors', 0)}")
    click.echo(f"  - Audio Errors: {report.failureSummary.get('audioErrors', 0)}")
    click.echo(f"  - A/V Sync Errors: {report.failureSummary.get('avSyncErrors', 0)}")
    click.echo(f"  - Other Errors: {report.failureSummary.get('otherErrors', 0)}")


def _colorizeStatus(text: str, status: ValidationStatus) -> str:
    """Colorize status text for terminal output."""
    if status == ValidationStatus.PASS:
        return click.style(text, fg="green")
    elif status == ValidationStatus.FAIL:
        return click.style(text, fg="red")
    else:
        return click.style(text, fg="yellow")


@click.group()
@click.version_option(version=__version__)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--log-dir", type=click.Path(), default="./logs", help="Directory for log files")
@click.pass_context
def main(ctx, verbose: bool, log_dir: str):
    """Video Quality Validator - Validate video files for AI/ML training data quality."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["log_dir"] = log_dir
    ctx.obj["validator"] = VideoQualityValidator(logDir=log_dir)


@main.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Choice(["text", "json", "both"]), default="text", help="Output format")
@click.option("--output-file", type=click.Path(), help="Write output to file instead of stdout")
@click.option("--skip-audio", is_flag=True, help="Skip audio validation")
@click.pass_context
def validate(ctx, video_path: str, output: str, output_file: Optional[str], skip_audio: bool):
    """Validate a single video file."""
    validator = ctx.obj["validator"]
    result = validator.validateSingle(video_path, skipAudio=skip_audio)

    output_content = ""

    if output in ["text", "both"]:
        # Capture text output
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            printTextResult(result)
        text_output = f.getvalue()
        output_content += text_output
        if output == "text":
            click.echo(text_output)

    if output in ["json", "both"]:
        json_output = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        output_content += "\n" + json_output
        if output == "json":
            click.echo(json_output)

    if output_file:
        Path(output_file).write_text(output_content, encoding="utf-8")

    # Set exit code
    if result.status == ValidationStatus.FAIL:
        sys.exit(1)
    elif not result.decodeIntegrityPass:
        sys.exit(2)


@main.command()
@click.argument("directory_path", type=click.Path(exists=True, file_okay=False))
@click.option("--recursive", "-r", is_flag=True, help="Search recursively in subdirectories")
@click.option("--extensions", "-e", help="Comma-separated list of video extensions")
@click.option("--output", "-o", type=click.Choice(["text", "json", "both"]), default="text", help="Output format")
@click.option("--output-dir", type=click.Path(file_okay=False), help="Directory to write output files")
@click.option("--skip-audio", is_flag=True, help="Skip audio validation")
@click.option("--parallel", "-p", type=int, default=1, help="Number of parallel tasks (default: 1)")
@click.pass_context
def batch_validate(ctx, directory_path: str, recursive: bool, extensions: Optional[str],
                   output: str, output_dir: Optional[str], skip_audio: bool, parallel: int):
    """Batch validate video files in a directory."""
    validator = ctx.obj["validator"]

    ext_list = None
    if extensions:
        ext_list = [e.strip() for e in extensions.split(",")]

    report = validator.validateBatch(
        directory_path,
        recursive=recursive,
        extensions=ext_list,
        skipAudio=skip_audio,
        parallel=parallel,
    )

    output_content = ""

    if output in ["text", "both"]:
        # Capture text output
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            printTextReport(report)
        text_output = f.getvalue()
        output_content += text_output
        if output == "text":
            click.echo(text_output)

    if output in ["json", "both"]:
        json_output = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
        output_content += "\n" + json_output
        if output == "json":
            click.echo(json_output)

    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "batch-results.txt").write_text(output_content, encoding="utf-8")
        (out_dir / "batch-results.json").write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
