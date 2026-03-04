#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visualization module for generating HTML reports.

This module provides functions for creating interactive HTML visualizations
of clip extraction results.
"""

import json
import os
from datetime import datetime
from pathlib import Path


def generateHtml(results, outputPath, title="Video Clip Analysis"):
    """
    Generate an HTML visualization of clip extraction results.

    Args:
        results: List of result dictionaries
        outputPath: Path to save the HTML file
        title: Title for the HTML page
    """
    htmlContent = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .summary {{
            background: #e8f5e9;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }}
        .video-item {{
            border: 1px solid #ddd;
            margin: 10px 0;
            padding: 15px;
            border-radius: 4px;
        }}
        .video-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            background: #f9f9f9;
            padding: 10px;
            margin: -15px -15px 15px -15px;
            border-radius: 4px 4px 0 0;
        }}
        .video-header:hover {{
            background: #f0f0f0;
        }}
        .clip-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        .clip-table th, .clip-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        .clip-table th {{
            background: #4CAF50;
            color: white;
        }}
        .clip-table tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        .action-id {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: bold;
            color: white;
        }}
        .hidden {{
            display: none;
        }}
        .timestamp {{
            font-family: monospace;
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        .footer {{
            margin-top: 20px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="summary">
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Total videos:</strong> {len(results)}</p>
        </div>
"""

    actionColors = [
        '#FF5722', '#2196F3', '#4CAF50', '#FF9800', '#9C27B0',
        '#00BCD4', '#FFEB3B', '#795548', '#E91E63', '#607D8B'
    ]

    for idx, result in enumerate(results):
        videoId = result.get('id', f'video_{idx}')
        clips = result.get('clips', [])
        videoPath = result.get('video_path', '')

        htmlContent += f"""
        <div class="video-item">
            <div class="video-header" onclick="toggleVideo({idx})">
                <h3>{videoId}</h3>
                <span>{len(clips)} clips</span>
            </div>
            <div id="video-{idx}" class="video-content">
                <p><strong>Path:</strong> {videoPath}</p>
                <table class="clip-table">
                    <tr>
                        <th>Index</th>
                        <th>Action ID</th>
                        <th>Start Time</th>
                        <th>End Time</th>
                        <th>Duration</th>
                        <th>Description</th>
                    </tr>
"""

        for clipIdx, clip in enumerate(clips):
            actionId = clip.get('action_id', 0)
            startTime = clip.get('start_time', '')
            endTime = clip.get('end_time', '')
            event = clip.get('event', '')
            color = actionColors[actionId % len(actionColors)]

            try:
                from src.utils.time_utils import time_to_seconds
                duration = time_to_seconds(endTime) - time_to_seconds(startTime)
                durationStr = f"{duration:.2f}s"
            except:
                durationStr = "-"

            htmlContent += f"""
                    <tr>
                        <td>{clipIdx}</td>
                        <td><span class="action-id" style="background: {color}">{actionId}</span></td>
                        <td><span class="timestamp">{startTime}</span></td>
                        <td><span class="timestamp">{endTime}</span></td>
                        <td>{durationStr}</td>
                        <td>{event}</td>
                    </tr>
"""

        htmlContent += """
                </table>
            </div>
        </div>
"""

    htmlContent += """
        <div class="footer">
            <p>Generated by SkyClipper</p>
        </div>
    </div>

    <script>
        function toggleVideo(idx) {
            const content = document.getElementById('video-' + idx);
            content.classList.toggle('hidden');
        }
    </script>
</body>
</html>
"""

    with open(outputPath, 'w', encoding='utf-8') as f:
        f.write(htmlContent)


def loadJsonlResults(jsonlPath):
    """
    Load results from a JSONL file.

    Args:
        jsonlPath: Path to JSONL file

    Returns:
        list: List of parsed JSON objects
    """
    results = []
    with open(jsonlPath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return results


def visualizeResults(jsonlPath, outputHtmlPath=None, title=None):
    """
    Visualize results from a JSONL file.

    Args:
        jsonlPath: Path to input JSONL file
        outputHtmlPath: Path to output HTML file (optional)
        title: Title for the HTML page (optional)
    """
    if outputHtmlPath is None:
        basePath = os.path.splitext(jsonlPath)[0]
        outputHtmlPath = f"{basePath}.html"

    if title is None:
        title = f"Video Clip Analysis - {os.path.basename(jsonlPath)}"

    results = loadJsonlResults(jsonlPath)
    generateHtml(results, outputHtmlPath, title)
    return outputHtmlPath


# Snake_case aliases for backward compatibility
generate_html = generateHtml
load_jsonl_results = loadJsonlResults
visualize_results = visualizeResults
