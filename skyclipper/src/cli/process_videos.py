#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI for processing videos with TransNet and Qwen3-VL.

This module provides a command-line interface for the main video processing
pipeline, orchestrating TransNet scene detection and Qwen3-VL action recognition.
"""

import os
import argparse
import torch.multiprocessing as mp

from src.core.video_processor import process_video_pipeline


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Parallel TransNet + Qwen3-VL Processing"
    )
    parser.add_argument(
        "--video_list",
        required=True,
        help="Path to CSV file containing video list"
    )
    parser.add_argument(
        "--output_jsonl",
        required=True,
        help="Path to output JSONL file"
    )
    parser.add_argument(
        "--model_path",
        default="/ai-video-nas-sh-b-2/mingshan.chang/models/Qwen3-VL-30B-A3B-Instruct",
        help="Path to Qwen3-VL model"
    )
    parser.add_argument(
        "--transnet_weights",
        default="/ai-video-nas-sh-b-2/yuqiang.xie/TransNetV2/transnetv2-pytorch-weights.pth",
        help="Path to TransNet weights file"
    )
    parser.add_argument(
        "--transnet_workers",
        type=int,
        default=8,
        help="Number of TransNet parallel workers (recommended: number of GPUs)"
    )
    parser.add_argument(
        "--transnet_threshold",
        type=float,
        default=0.1,
        help="TransNet scene detection threshold (lower=more scenes, 0.15-0.20 for anime)"
    )
    parser.add_argument(
        "--queue_batch_size",
        type=int,
        default=16,
        help="Queue accumulation size (number of videos to collect before processing)"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=16,
        help="Qwen3-VL inference batch size (segments per inference)"
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=2.0,
        help="Frames per second for video sampling"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=360,
        help="Video width for processing"
    )
    parser.add_argument(
        "--max_segment_seconds",
        type=int,
        default=120,
        help="Maximum segment duration in seconds"
    )
    parser.add_argument(
        "--max_frames_per_segment",
        type=int,
        default=240,
        help="Maximum frames per segment"
    )
    parser.add_argument(
        "--skip_start_seconds",
        type=int,
        default=120,
        help="Seconds to skip from start of video"
    )
    parser.add_argument(
        "--skip_end_seconds",
        type=int,
        default=120,
        help="Seconds to skip from end of video"
    )
    parser.add_argument(
        "--no_segment_split",
        action="store_true",
        help="Don't split segments, process entire video as single segment"
    )
    parser.add_argument(
        "--transnet_cache_dir",
        default="/ai-video-nas-sh-b-2/yuqiang.xie/smart_clipper/output/anime_2025-12-13_test_transnet/transnet_cache",
        help="Directory to cache TransNet results"
    )
    parser.add_argument(
        "--node_rank",
        type=int,
        default=0,
        help="Node rank for multi-node processing"
    )
    parser.add_argument(
        "--num_nodes",
        type=int,
        default=1,
        help="Total number of nodes for multi-node processing"
    )
    parser.add_argument(
        "--videos_per_batch",
        type=int,
        default=100,
        help="Number of videos per batch for progress display"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint (skip already processed videos)"
    )

    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.video_list):
        print(f"Error: Video list file does not exist: {args.video_list}")
        return

    # Run the pipeline
    process_video_pipeline(args.video_list, args.output_jsonl, args)


if __name__ == "__main__":
    mp.set_start_method('spawn', force=True)
    main()
