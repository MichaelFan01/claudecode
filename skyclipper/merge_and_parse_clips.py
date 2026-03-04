#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
汇总、解析和合并所有节点的输出结果（并行版本）- 针对 YouTube Sports 数据

功能：
1. 读取 youtube_sports_batch_1_clips_temp 目录下所有 node_*.jsonl 文件
2. 并行处理每个node文件，生成shot和scene两个级别的结果
3. 合并所有结果（按video_id去重）
4. 生成两个输出文件：
   - video_clips_shot.jsonl: shot级别（原始clips，不合并）
   - video_clips_scene.jsonl: scene级别（3-10秒合并后的clips）

使用方法：
    python merge_and_parse_clips.py

    或指定参数：
    python merge_and_parse_clips.py \
        --temp_dir /path/to/youtube_sports_batch_1_clips_temp \
        --output_shot /path/to/video_clips_shot.jsonl \
        --output_scene /path/to/video_clips_scene.jsonl \
        --min_duration 5.0 \
        --max_duration 15.0 \
        --num_workers 8

NOTE: This is a compatibility wrapper. For new code, use:
python -m src.cli.merge_results --temp_dir <dir> --output_shot <shot> --output_scene <scene>
"""

# Import from the new modular structure
from src.cli.merge_results import main


if __name__ == "__main__":
    main()
