# CLI Interface Contracts

## process-videos (Main Video Processing)

**Command**: `python src/cli/process-videos.py [OPTIONS]`

### Input CSV Format
```csv
video_path,fps,duration
/path/to/video1.mp4,30,120.5
/path/to/video2.mp4,24,95.3
```

### Options
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--input_csv` | string | required | Path to input CSV file |
| `--output_dir` | string | `./output` | Output directory |
| `--model_path` | string | required | Path to Qwen3-VL model |
| `--transnet_weights` | string | `./transnetv2-pytorch-weights.pth` | Path to TransNet weights |
| `--transnet_workers` | integer | 8 | Number of TransNet workers |
| `--transnet_threshold` | float | 0.2 | Scene detection threshold |
| `--batch_size` | integer | 16 | Qwen3-VL batch size |
| `--fps` | float | 2.0 | Sampling frame rate |
| `--width` | integer | 360 | Video width for processing |
| `--language` | string | `zh` | Output language (zh/en) |
| `--prompt_template` | string | optional | Custom prompt template path |

### Output Format (JSONL)
```json
{
  "video_id": "abc123",
  "video_path": "/path/to/video.mp4",
  "segment_id": 0,
  "clip_id": 1,
  "action_id": 1,
  "action_desc": "人物在街上行走",
  "clip_desc": "全景镜头展示人物从左向右穿过街道",
  "start_time": "00:00:05.200",
  "end_time": "00:00:09.800",
  "duration": 4.6
}
```

---

## merge-results (Result Merging)

**Command**: `python src/cli/merge-results.py [OPTIONS]`

### Options
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--temp_dir` | string | `./output/temp` | Directory with node_*.jsonl files |
| `--output_shot` | string | `./output/video_clips_shot.jsonl` | Shot-level output |
| `--output_scene` | string | `./output/video_clips_scene.jsonl` | Scene-level output |
| `--min_duration` | float | 5.0 | Minimum scene duration (seconds) |
| `--max_duration` | float | 15.0 | Maximum scene duration (seconds) |
| `--num_workers` | integer | 8 | Number of parallel workers |

### Scene Output Format
```json
{
  "video_id": "abc123",
  "video_path": "/path/to/video.mp4",
  "scene_id": 1,
  "action_desc": "人物在街上行走",
  "scene_desc": "全景镜头展示人物从左向右穿过街道，随后切换到人物正面特写",
  "start_time": "00:00:05.200",
  "end_time": "00:00:15.400",
  "duration": 10.2,
  "num_clips": 2
}
```

---

## visualize (Visualization)

**Command**: `python src/cli/visualize.py [OPTIONS]`

### Options
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--jsonl` | string | required | Path to input JSONL file (shot or scene) |
| `--output` | string | `./output/viewer.html` | Output HTML file |

### Output HTML Features
- Video playback per segment
- Timeline visualization
- Action description display
- Quality review controls
