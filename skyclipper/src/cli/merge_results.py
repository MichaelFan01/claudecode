#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI for merging and parsing clip extraction results.

This module provides a command-line interface for merging and processing
clip extraction results from multiple nodes.
"""

import os
import argparse

from src.core.result_merger import (
    parallel_process_node_files,
    merge_temp_files
)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Parallel merge, parse, and combine results from all nodes"
    )
    parser.add_argument(
        "--temp_dir",
        default="/ai-video-nas-sh-b-2/yuqiang.xie/smart_clipper/output/anime_multinode_part3/output_temp",
        help="Temporary directory path (containing node_*.jsonl files)"
    )
    parser.add_argument(
        "--output_shot",
        default="/ai-video-nas-sh-b-2/yuqiang.xie/smart_clipper/output/anime_multinode_part3/anime_2025-12-24_shot_part3.jsonl",
        help="Shot-level output file path"
    )
    parser.add_argument(
        "--output_scene",
        default="/ai-video-nas-sh-b-2/yuqiang.xie/smart_clipper/output/anime_multinode_part3/anime_2025-12-24_action_5_15s_part3.jsonl",
        help="Scene-level output file path"
    )
    parser.add_argument(
        "--min_duration",
        type=float,
        default=5.0,
        help="Minimum duration for scene merging (seconds), default 5 seconds"
    )
    parser.add_argument(
        "--max_duration",
        type=float,
        default=15.0,
        help="Maximum duration for scene merging (seconds), default 15 seconds"
    )
    parser.add_argument(
        "--num_workers",
        type=int,
        default=8,
        help="Number of parallel processes, default 8"
    )
    parser.add_argument(
        "--keep_temp",
        action="store_true",
        help="Keep temporary files (for debugging)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.temp_dir):
        print(f"Error: Directory does not exist: {args.temp_dir}")
        return

    outputDir = os.path.dirname(args.output_shot) if os.path.dirname(args.output_shot) else "."
    os.makedirs(outputDir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Parallel Processing Mode - YouTube Sports Data")
    print(f"{'='*60}")
    print(f"Input directory: {args.temp_dir}")
    print(f"Shot output: {args.output_shot}")
    print(f"Scene output: {args.output_scene}")
    print(f"Duration range: {args.min_duration}-{args.max_duration} seconds")
    print(f"Parallel processes: {args.num_workers or 'CPU cores'}")
    print(f"{'='*60}\n")

    resultsDir = outputDir

    print("\n【Step 1/3】Processing node files in parallel...")
    stats = parallel_process_node_files(
        args.temp_dir,
        resultsDir,
        min_duration_seconds=args.min_duration,
        max_duration_seconds=args.max_duration,
        num_workers=args.num_workers
    )

    if not stats or stats.get('total_shot', 0) == 0:
        print("Error: No data processed")
        return

    print("\n【Step 2/3】Merging shot temporary files...")
    shotCount = merge_temp_files(
        resultsDir,
        args.output_shot,
        "node_*_shot.jsonl"
    )
    print(f"  Shot output: {args.output_shot}")
    print(f"  Record count: {shotCount}")

    print("\n【Step 3/3】Merging scene temporary files...")
    sceneCount = merge_temp_files(
        resultsDir,
        args.output_scene,
        "node_*_scene.jsonl"
    )
    print(f"  Scene output: {args.output_scene}")
    print(f"  Record count: {sceneCount}")

    if not args.keep_temp:
        print("\nCleaning up temporary files...")
        import glob
        tempPattern = os.path.join(resultsDir, "node_*_shot.jsonl")
        tempFiles = glob.glob(tempPattern)
        tempPattern2 = os.path.join(resultsDir, "node_*_scene.jsonl")
        tempFiles.extend(glob.glob(tempPattern2))

        deletedCount = 0
        for tempFile in tempFiles:
            try:
                os.remove(tempFile)
                deletedCount += 1
            except Exception as e:
                print(f"  Warning: Failed to delete temporary file {tempFile}: {e}")

        print(f"  Deleted {deletedCount} temporary files")

    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"{'='*60}")
    print(f"Total time: {stats.get('elapsed_time', 0):.2f} seconds ({stats.get('elapsed_time', 0)/60:.2f} minutes)")
    print(f"Shot records: {shotCount}")
    print(f"Scene records: {sceneCount}")
    print(f"Error records: {stats.get('total_errors', 0)}")
    if stats.get('failed_nodes'):
        print(f"Failed nodes: {', '.join(stats['failed_nodes'])}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
