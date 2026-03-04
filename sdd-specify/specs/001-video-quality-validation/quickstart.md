# Quickstart: 视频质量验证模块

**Date**: 2026-03-03
**Feature**: 001-video-quality-validation

## Prerequisites

- Python 3.11 or higher
- FFmpeg installed on your system

## Installation

```bash
# Install the package
pip install video-quality-validator

# Verify installation
video-quality-validator --version
```

## Quick Start (5 minutes or less)

### 1. Validate a single video file

```bash
# Basic validation
video-quality-validator validate /path/to/your/video.mp4

# Save JSON output
video-quality-validator validate /path/to/your/video.mp4 --output json --output-file result.json
```

### 2. Batch validate a directory

```bash
# Validate all videos in a directory
video-quality-validator batch-validate /path/to/videos/

# Recursively validate with 4 parallel tasks
video-quality-validator batch-validate /path/to/videos/ --recursive --parallel 4
```

### 3. Check logs

All operations are logged to the `./logs` directory by default:

```bash
# View recent logs
ls -la ./logs/
tail -f ./logs/validation-2026-03-03.log
```

## Common Use Cases

### AI Model Training Data Preparation

```bash
# Validate your training dataset before use
video-quality-validator batch-validate ./training-data/videos/ --recursive --output both
```

### Quality Control Pipeline

```bash
# Integrate into your pipeline with JSON output for parsing
video-quality-validator validate ./input.mp4 --output json > validation-result.json
```

## Troubleshooting

### FFmpeg not found

Install FFmpeg first:
- macOS: `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt-get install ffmpeg`
- Windows: Download from https://ffmpeg.org/download.html

### Unsupported video format

The module supports: mp4, avi, mov, webm, mkv by default. You can specify additional extensions:

```bash
video-quality-validator batch-validate ./videos/ --extensions "mp4,avi,mov,webm,mkv,flv"
```

## Next Steps

- See the full documentation for advanced usage
- Check the Python API for library integration
- Review the constitution for project standards
