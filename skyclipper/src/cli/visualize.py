#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI for visualizing clip extraction results.

This module provides a command-line interface for generating HTML
visualizations of clip extraction results.
"""

import os
import argparse

from src.core.visualizer import visualize_results


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate HTML visualization from clip extraction results"
    )
    parser.add_argument(
        "input_jsonl",
        help="Input JSONL file with clip extraction results"
    )
    parser.add_argument(
        "--output_html",
        default=None,
        help="Output HTML file path (optional, defaults to input with .html extension)"
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Title for the HTML page (optional)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.input_jsonl):
        print(f"Error: Input file does not exist: {args.input_jsonl}")
        return

    print(f"\n{'='*60}")
    print(f"Generating visualization...")
    print(f"{'='*60}")
    print(f"Input: {args.input_jsonl}")

    outputPath = visualize_results(args.input_jsonl, args.output_html, args.title)

    print(f"Output: {outputPath}")
    print(f"{'='*60}")
    print(f"✓ Visualization complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
