# CLI Contracts: 视频质量验证模块

**Date**: 2026-03-03
**Feature**: 001-video-quality-validation

## Command Line Interface

### Main Command: video-quality-validator

**Usage**:
```bash
video-quality-validator [OPTIONS] COMMAND [ARGS]...
```

**Global Options**:
- `--help`: Show help message and exit
- `--version`: Show version and exit
- `--verbose / -v`: Enable verbose output
- `--log-dir PATH`: Directory for log files (default: ./logs)

---

### Command 1: validate

验证单个视频文件。

**Usage**:
```bash
video-quality-validator validate [OPTIONS] VIDEO_PATH
```

**Arguments**:
- `VIDEO_PATH`: Path to video file (required)

**Options**:
- `--output TEXT`: Output format - "text", "json", or "both" (default: "text")
- `--output-file PATH`: Write output to file instead of stdout
- `--skip-audio`: Skip audio validation even if audio track exists
- `--help`: Show help message and exit

**Output Example (Text)**:
```
Video Validation Result
=======================
File: /path/to/video.mp4
Status: PASS
Timestamp: 2026-03-03T10:30:00

Video Properties:
  - Frame Rate: 30.0 FPS ✓
  - Total Frames: 1800 ✓
  - Decode Integrity: PASS ✓

Audio Properties:
  - Has Audio: Yes
  - Sample Rate: 44100 Hz ✓
  - Channels: 2 ✓
  - Duration: 60.0s
  - A/V Sync: PASS ✓

Duration: 2.3s
```

**Output Example (JSON)**:
```json
{
  "filePath": "/path/to/video.mp4",
  "timestamp": "2026-03-03T10:30:00",
  "status": "PASS",
  "frameRate": 30.0,
  "frameRatePass": true,
  "totalFrames": 1800,
  "totalFramesPass": true,
  "decodeIntegrityPass": true,
  "hasAudio": true,
  "audioSampleRate": 44100,
  "audioSampleRatePass": true,
  "audioChannels": 2,
  "audioChannelsPass": true,
  "videoDuration": 60.0,
  "audioDuration": 60.0,
  "avSyncPass": true,
  "validationErrors": []
}
```

**Exit Codes**:
- `0`: Validation completed and video passed
- `1`: Validation completed but video failed
- `2`: Validation error occurred (file not found, unsupported format, etc.)

---

### Command 2: batch-validate

批量验证目录中的视频文件。

**Usage**:
```bash
video-quality-validator batch-validate [OPTIONS] DIRECTORY_PATH
```

**Arguments**:
- `DIRECTORY_PATH`: Path to directory containing video files (required)

**Options**:
- `--recursive / -r`: Search recursively in subdirectories
- `--extensions TEXT`: Comma-separated list of video extensions (default: "mp4,avi,mov,webm,mkv")
- `--output TEXT`: Output format - "text", "json", or "both" (default: "text")
- `--output-dir PATH`: Directory to write output files (default: current directory)
- `--skip-audio`: Skip audio validation for all files
- `--parallel INTEGER`: Number of parallel validation tasks (default: 1)
- `--help`: Show help message and exit

**Output Example (Summary Text)**:
```
Batch Validation Report
========================
Start Time: 2026-03-03T10:00:00
End Time: 2026-03-03T10:05:30
Duration: 5m 30s

Summary:
  - Total Files: 10
  - Passed: 8
  - Failed: 1
  - Partial: 1
  - Pass Rate: 80%

Failure Breakdown:
  - Decode Errors: 1
  - Audio Errors: 1
  - A/V Sync Errors: 0
  - Other Errors: 0

Detailed results written to: batch-results.json
```

**Output Example (JSON)**:
```json
{
  "reportId": "batch-20260303-100000",
  "startTime": "2026-03-03T10:00:00",
  "endTime": "2026-03-03T10:05:30",
  "totalFiles": 10,
  "passedFiles": 8,
  "failedFiles": 1,
  "partialFiles": 1,
  "results": [
    {
      "filePath": "/path/to/video1.mp4",
      "status": "PASS",
      "timestamp": "2026-03-03T10:00:02"
    }
  ],
  "failureSummary": {
    "decodeErrors": 1,
    "frameRateErrors": 0,
    "audioErrors": 1,
    "avSyncErrors": 0,
    "otherErrors": 0
  }
}
```

**Exit Codes**:
- `0`: Batch validation completed
- `1`: Batch validation error occurred

---

## Python Library API

### Class: VideoQualityValidator

Main class for video quality validation.

**Methods**:
- `__init__(log_dir: str = "./logs")`
- `validate_single(video_path: str, skip_audio: bool = False) -> VideoValidationResult`
- `validate_batch(directory_path: str, recursive: bool = False, extensions: List[str] = None, skip_audio: bool = False, parallel: int = 1) -> BatchValidationReport`

### Exceptions

- `VideoFileNotFoundError`: Video file not found
- `UnsupportedVideoFormatError`: Video format not supported
- `VideoDecodeError`: Video decoding failed
- `AudioValidationError`: Audio validation failed
