# Quickstart: SkyClipper

**Feature**: 001-refactor-codebase | **Date**: 2026-03-04

## Prerequisites

- Python 3.8+
- CUDA-capable GPUs (for full functionality)
- PyTorch with CUDA support

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd skyclipper

# Install dependencies
pip install -r requirements.txt

# Download model weights (if needed)
# Qwen3-VL model
# TransNetV2 weights
```

## 5-Minute Quickstart

### 1. Prepare Input Data

Create a CSV file with your video paths:

```csv
video_path,fps,duration
/path/to/my-video.mp4,30,120.5
```

### 2. Run Video Processing (Single Node)

```bash
bash run-singlenode.sh
```

### 3. Merge Results

```bash
python merge_and_parse_clips.py \
    --temp_dir output/temp \
    --output_shot output/video_clips_shot.jsonl \
    --output_scene output/video_clips_scene.jsonl
```

### 4. Visualize Results

```bash
python parser_vis.py \
    --jsonl output/video_clips_scene.jsonl \
    --output viewer.html
```

Open `viewer.html` in your browser to review the results.

---

## Using the New Modular CLI (Post-Refactor)

After refactoring is complete, you can also use the new modular commands:

```bash
# Process videos
python -m src.cli.process-videos \
    --input_csv input.csv \
    --output_dir output \
    --model_path /path/to/qwen3-vl

# Merge results
python -m src.cli.merge-results \
    --temp_dir output/temp \
    --output_scene output/scenes.jsonl

# Visualize
python -m src.cli.visualize \
    --jsonl output/scenes.jsonl \
    --output viewer.html
```

---

## Key Concepts

- **Shot**: Raw camera clip detected by TransNet
- **Scene**: Merged semantic segment (5-15 seconds)
- **Action**: What's happening in the video segment

## Troubleshooting

**GPU out of memory**: Reduce `--batch_size` or `--width`

**Slow processing**: Increase `--transnet_workers` or reduce `--fps`

See [README.md](../../README.md) for complete documentation.
