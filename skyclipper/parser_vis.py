#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parse and visualize video clips from Qwen3-VL results.

功能：
1. 读取JSONL或CSV结果文件
2. 提取视频片段
3. 生成HTML可视化页面

使用方法：
    python parser_vis.py --jsonl video_clips_scene.jsonl
    python parser_vis.py --result_csv results.csv

NOTE: This is a compatibility wrapper that preserves the original functionality.
The core visualization logic is now in src.core.visualizer.
"""

import sys
import os

# Add the current directory to path to make sure we can import the original code
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check if we're being run as a script
if __name__ == "__main__":
    # This is a compatibility wrapper - we'll keep the original implementation
    # since it has more features (video extraction, etc.) that aren't yet
    # in the modular visualizer module.

    # The following is the original parser_vis.py code preserved for compatibility.
    # In the future, this could be refactored into src/cli/extract_and_visualize.py

    import argparse
    import json
    import re
    import subprocess
    import concurrent.futures
    import pandas as pd
    from datetime import datetime


    # 是否启用合并相邻相同 action 的片段逻辑（默认关闭，可用环境变量覆盖）
    # 设置环境变量 SKYCLIPPER_USE_MERGE=1 可开启
    USE_MERGE_ACTION_CLIPS = os.environ.get('SKYCLIPPER_USE_MERGE', '0') in ('1', 'true', 'True')


    def parse_xml_clips(xml_text):
        """解析XML格式的clip输出，支持可选的<action_desc>字段（向后兼容）"""
        clips = []

        # 移除```xml标记
        if '```xml' in xml_text:
            xml_text = xml_text.split('```xml')[1]
        if '```' in xml_text:
            xml_text = xml_text.split('```')[0]

        # 使用正则表达式提取clip信息，支持可选<action_desc>
        # 捕获顺序：time, action, action_desc(可选), description
        clip_pattern_with_desc = r'<clip>\s*<time>(.*?)</time>\s*<action>(.*?)</action>\s*(?:<action_desc>(.*?)</action_desc>\s*)?(.*?)\s*</clip>'
        matches = re.findall(clip_pattern_with_desc, xml_text, re.DOTALL)

        print(f"Found {len(matches)} XML clips in text")

        for i, match in enumerate(matches):
            time_str, action_id, action_desc, description = match
            time_str = time_str.strip()
            description = description.strip()
            action_desc = (action_desc or '').strip()

            # 解析时间范围
            if '-' in time_str:
                start_time, end_time = time_str.split('-', 1)  # 只分割第一个'-'
                start_time = start_time.strip()
                end_time = end_time.strip()
            else:
                print(f"Warning: Invalid time format: {time_str}")
                continue

            # 验证时间格式
            try:
                time_to_seconds(start_time)
                time_to_seconds(end_time)
            except:
                print(f"Warning: Invalid time values: {start_time} - {end_time}")
                continue

            clip_item = {
                'start_time': start_time,
                'end_time': end_time,
                'action_id': int(action_id.strip()),
                'event': description
            }
            if action_desc:
                clip_item['action_desc'] = action_desc
            clips.append(clip_item)

        return clips


    def time_to_seconds(time_str):
        """将时间字符串转换为秒数"""
        # 支持格式: HH:MM:SS.mmm 或 HH:MM:SS,mmm
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds


    def normalize_time_format(time_str):
        """标准化时间格式，确保是 HH:MM:SS.mmm"""
        try:
            total_seconds = time_to_seconds(time_str)
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = total_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
        except:
            return time_str


    def unescape_csv_content(content):
        """反转义CSV中的内容"""
        if pd.isna(content):
            return ""
        content = str(content)
        # 替换转义的引号
        content = content.replace('""', '"')
        # 如果首尾有引号且内部有引号，则移除首尾引号
        if content.startswith('"') and content.endswith('"'):
            # 检查是否是标准的CSV转义
            inner_content = content[1:-1]
            if '""' in inner_content:
                return inner_content.replace('""', '"')
        return content


    def extract_video_clip(input_video, start_time, end_time, output_video):
        """使用ffmpeg提取视频片段"""
        try:
            # 使用ffmpeg提取片段，精确到帧
            cmd = [
                'ffmpeg',
                '-ss', start_time,
                '-to', end_time,
                '-i', input_video,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-y',  # 覆盖输出文件
                output_video
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                print(f"ffmpeg error: {result.stderr}")
                return False
            return True
        except Exception as e:
            print(f"Error extracting clip: {e}")
            return False


    def extract_video_clips(video_path, clips, output_dir):
        """从视频中提取多个片段"""
        extracted_clips = []

        # 生成唯一的视频ID（使用父目录+文件名）
        video_basename = os.path.basename(video_path)
        parent_dir = os.path.basename(os.path.dirname(video_path))
        video_id = f"{parent_dir}_{os.path.splitext(video_basename)[0]}"

        for idx, clip in enumerate(clips):
            start_time = clip['start_time']
            end_time = clip['end_time']

            # 生成输出文件名
            clip_filename = f"{video_id}_clip_{idx:03d}_{start_time.replace(':', '-')}_to_{end_time.replace(':', '-')}.mp4"
            clip_path = os.path.join(output_dir, clip_filename)

            # 提取片段
            success = extract_video_clip(video_path, start_time, end_time, clip_path)

            if success:
                extracted_clip = clip.copy()
                extracted_clip['clip_index'] = idx
                extracted_clip['clip_path'] = clip_path
                extracted_clips.append(extracted_clip)

        return extracted_clips


    def fill_small_gaps_before_merge(clips, max_gap_seconds=0.5):
        """合并前填充小间隙（确保相邻片段时间连续）"""
        if len(clips) < 2:
            return clips

        filled_clips = []
        for i in range(len(clips)):
            current_clip = clips[i].copy()

            if i > 0:
                prev_clip = filled_clips[-1]
                prev_end = time_to_seconds(prev_clip['end_time'])
                curr_start = time_to_seconds(current_clip['start_time'])
                gap = curr_start - prev_end

                # 如果间隙很小，填充它
                if 0 < gap < max_gap_seconds:
                    prev_clip['end_time'] = current_clip['start_time']

            filled_clips.append(current_clip)

        return filled_clips


    def merge_action_clips(clips, min_duration=5, max_duration=20):
        """合并相邻的相同action片段"""
        if len(clips) < 2:
            return clips

        merged = []
        current_group = [clips[0]]

        for i in range(1, len(clips)):
            current_clip = clips[i]
            last_clip = current_group[-1]

            # 检查是否可以合并：
            # 1. 相同的action_id
            # 2. 时间上连续或重叠
            # 3. 合并后不超过max_duration

            same_action = current_clip.get('action_id') == last_clip.get('action_id')

            # 检查时间连续性
            last_end = time_to_seconds(last_clip['end_time'])
            curr_start = time_to_seconds(current_clip['start_time'])
            gap = curr_start - last_end

            # 计算合并后的时长
            group_start = time_to_seconds(current_group[0]['start_time'])
            group_end = time_to_seconds(current_clip['end_time'])
            merged_duration = group_end - group_start

            # 合并条件：
            # - 相同action
            # - 间隙小于1秒
            # - 合并后不超过max_duration
            if same_action and gap < 1.0 and merged_duration <= max_duration:
                current_group.append(current_clip)
            else:
                # 不能合并，先保存当前组
                if len(current_group) > 1:
                    # 合并组内的片段
                    merged_clip = current_group[0].copy()
                    merged_clip['end_time'] = current_group[-1]['end_time']
                    # 合并描述（保留第一个）
                    merged.append(merged_clip)
                else:
                    merged.append(current_group[0])
                current_group = [current_clip]

        # 处理最后一个组
        if len(current_group) > 1:
            merged_clip = current_group[0].copy()
            merged_clip['end_time'] = current_group[-1]['end_time']
            merged.append(merged_clip)
        else:
            merged.append(current_group[0])

        return merged


    def generate_html_viewer(clips_df, clips_dir, result_csv_path):
        """生成HTML可视化页面"""
        print("Generating HTML viewer...")

        # 获取唯一视频列表
        unique_videos = clips_df['video_path'].unique()

        # 构建HTML
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Clips Viewer</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: #f0f0f0;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: #4CAF50;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 15px;
        }}
        .controls {{
            margin: 20px 0;
            padding: 15px;
            background: #2d2d2d;
            border-radius: 8px;
        }}
        .search-box {{
            width: 300px;
            padding: 10px;
            border: 1px solid #444;
            border-radius: 4px;
            background: #333;
            color: white;
            font-size: 14px;
        }}
        .search-box::placeholder {{
            color: #888;
        }}
        .filter-select {{
            margin-left: 15px;
            padding: 10px;
            border: 1px solid #444;
            border-radius: 4px;
            background: #333;
            color: white;
            font-size: 14px;
        }}
        .video-section {{
            margin: 20px 0;
            background: #2d2d2d;
            border-radius: 8px;
            overflow: hidden;
        }}
        .video-header {{
            padding: 15px;
            background: #444;
            font-weight: bold;
            font-size: 16px;
        }}
        .clips-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            padding: 15px;
        }}
        .clip-card {{
            background: #333;
            border-radius: 8px;
            overflow: hidden;
            transition: transform 0.2s;
        }}
        .clip-card:hover {{
            transform: scale(1.02);
        }}
        .video-placeholder {{
            width: 100%;
            aspect-ratio: 16/9;
            background: #000;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            position: relative;
        }}
        .video-placeholder:hover {{
            background: #111;
        }}
        .video-placeholder::before {{
            content: '▶️ 点击加载视频';
            color: rgba(255,255,255,0.7);
            font-size: 14px;
        }}
        .clip-video {{
            width: 100%;
            display: block;
        }}
        .clip-info {{
            padding: 10px;
        }}
        .clip-time {{
            color: #888;
            font-size: 12px;
            margin-bottom: 5px;
        }}
        .clip-description {{
            font-size: 13px;
            line-height: 1.4;
        }}
        .action-badge {{
            display: inline-block;
            background: #4CAF50;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-left: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Video Clips Viewer</h1>

        <div class="controls">
            <input type="text" class="search-box" placeholder="搜索片段描述..." onkeyup="filterClips()">
            <select class="filter-select" onchange="filterByVideo()">
                <option value="">所有视频</option>
"""

        # 添加视频选项
        for video_path in unique_videos:
            video_basename = os.path.basename(video_path)
            parent_dir = os.path.basename(os.path.dirname(video_path))
            video_display_name = f"{parent_dir}/{video_basename}"
            video_unique_id = f"{parent_dir}_{os.path.splitext(video_basename)[0]}"
            html_content += f"""
                <option value="{video_unique_id}">{video_display_name}</option>
"""

        html_content += """
            </select>
        </div>
"""

        # 按视频分组显示片段
        for video_path in unique_videos:
            # 使用父目录+文件名作为唯一标识
            video_basename = os.path.basename(video_path)
            parent_dir = os.path.basename(os.path.dirname(video_path))
            video_display_name = f"{parent_dir}/{video_basename}"
            video_unique_id = f"{parent_dir}_{os.path.splitext(video_basename)[0]}"
            video_clips = clips_df[clips_df['video_path'] == video_path]

            html_content += f"""
            <div class="video-section" data-video="{video_unique_id}">
                <div class="video-header">
                    {video_display_name} ({len(video_clips)} 个片段)
                </div>
                <div class="clips-grid">
"""

            for _, clip in video_clips.iterrows():
                # 构建视频文件路径（使用唯一ID）
                clip_filename = f"{video_unique_id}_clip_{clip['clip_index']:03d}_{clip['start_time'].replace(':', '-')}_to_{clip['end_time'].replace(':', '-')}.mp4"
                clip_path = os.path.join(clips_dir, clip_filename)
                relative_clip_path = os.path.relpath(clip_path, os.path.dirname(result_csv_path))

                action_desc_text = clip.get('action_desc', '') if isinstance(clip.get('action_desc', ''), str) else ''
                html_content += f"""
                    <div class="clip-card" data-description="{clip['event'].lower()}" data-action="{clip.get('action_id', 'N/A')}" data-action-desc="{action_desc_text}">
                        <div class="video-placeholder" data-src="{relative_clip_path}" onclick="loadVideo(this)">
                        </div>
                        <div class="clip-info">
                            <div class="clip-time">
                                片段 {clip['clip_index']}: {clip['start_time']} - {clip['end_time']}
                                <span class="action-badge">Action {clip.get('action_id', 'N/A')} {('· ' + action_desc_text) if action_desc_text else ''}</span>
                            </div>
                            <div class="clip-description">
                                {clip['event']}
                            </div>
                        </div>
                    </div>
"""

            html_content += """
                </div>
            </div>
"""

        html_content += """
        </div>
    </div>

    <script>
// 懒加载视频功能 - 参考simple_viewer_new.html实现
function loadVideo(placeholder) {
    const src = placeholder.getAttribute('data-src');
    if (!src) return;

    // 显示加载状态
    placeholder.innerHTML = `
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: white; text-align: center; z-index: 5;">
            <div style="border: 3px solid rgba(255,255,255,0.3); border-radius: 50%; border-top: 3px solid white; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 0 auto 10px;"></div>
            正在加载视频...
        </div>
    `;

    // 创建video元素
    const video = document.createElement('video');
    video.className = 'clip-video';
    video.controls = true;
    video.preload = 'metadata';

    const source = document.createElement('source');
    source.src = src;
    source.type = 'video/mp4';

    video.appendChild(source);
    video.appendChild(document.createTextNode('您的浏览器不支持视频播放。'));

    // 视频加载成功事件
    video.addEventListener('loadeddata', function() {
        placeholder.innerHTML = '';
        placeholder.appendChild(video);
    });

    // 视频加载失败事件
    video.addEventListener('error', function() {
        placeholder.innerHTML = `
            <div style="text-align: center; color: white;">
                ❌ 视频加载失败<br>
                <small>请检查网络连接或视频文件</small>
                <br><br>
                <button onclick="loadVideo(this.parentElement)" style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                    重试
                </button>
            </div>
        `;
    });

    // 设置视频源并开始加载
    video.load();
}

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

function filterClips() {
    const searchTerm = document.querySelector('.search-box').value.toLowerCase();
    const cards = document.querySelectorAll('.clip-card');

    cards.forEach(card => {
        const description = card.getAttribute('data-description');
        if (description.includes(searchTerm)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

function filterByVideo() {
    const selectedVideo = document.querySelector('.filter-select').value;
    const sections = document.querySelectorAll('.video-section');

    sections.forEach(section => {
        const videoName = section.getAttribute('data-video');
        if (selectedVideo === '' || videoName === selectedVideo) {
            section.style.display = 'block';
        } else {
            section.style.display = 'none';
        }
    });
}
    </script>
</body>
</html>
"""

        # 保存HTML文件
        html_path = os.path.join(os.path.dirname(result_csv_path), "video_clips_viewer.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Generated HTML viewer: {html_path}")


    def process_jsonl_file(jsonl_path, output_dir=None, limit=None):
        """处理jsonl文件，提取clips并生成可视化

        改进：合并同一视频的所有segments的clips，一起可视化

        Args:
            jsonl_path: jsonl文件路径
            output_dir: 输出目录，如果为None则使用jsonl文件所在目录
            limit: 限制处理的视频数量（不是segment数量）
        """
        print(f"Processing JSONL file: {jsonl_path}")
        if limit:
            print(f"Limiting to first {limit} videos")

        if output_dir is None:
            output_dir = os.path.dirname(jsonl_path)

        if not os.path.exists(jsonl_path):
            print(f"Error: JSONL file not found: {jsonl_path}")
            return

        # 创建video_clips目录
        clips_dir = os.path.join(output_dir, "video_clips")
        os.makedirs(clips_dir, exist_ok=True)

        # 第一步：读取所有segments，按video_id分组
        print("Step 1: Reading and grouping segments by video_id...")
        video_segments = {}  # {video_id: [segment_data, ...]}

        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    video_id = data.get('id', '')
                    video_path = data.get('video_path', '')

                    if not video_id or not video_path:
                        print(f"Warning: Line {line_num} missing video_id or video_path, skipping")
                        continue

                    # 按video_id分组
                    if video_id not in video_segments:
                        video_segments[video_id] = []
                    video_segments[video_id].append(data)
                except Exception as e:
                    print(f"Warning: Failed to parse line {line_num}: {e}")
                    continue

        print(f"Found {len(video_segments)} unique videos")

        # 如果有limit，只处理前limit个视频
        if limit:
            video_ids = list(video_segments.keys())[:limit]
            video_segments = {vid: video_segments[vid] for vid in video_ids}
            print(f"Limiting to first {limit} videos")

        # 第二步：合并同一视频的所有clips
        print("Step 2: Merging clips from all segments for each video...")
        video_clips_merged = {}  # {video_id: {'path': ..., 'clips': [...]}}

        for video_id, segments in video_segments.items():
            # 获取视频路径（使用第一个segment的路径）
            video_path = segments[0].get('video_path', '')

            # 检查路径是否存在，如果不存在且以特定前缀开头，则替换路径
            original_video_path = video_path
            if not os.path.exists(video_path):
                if video_path.startswith("/maindata/data/shared/public/"):
                    new_path = video_path.replace("/maindata/data/shared/public/", "/ai-video-nas-sh-b-2/", 1)
                    if os.path.exists(new_path):
                        video_path = new_path
                        print(f"Path replaced - Original: {original_video_path}")
                        print(f"Path replaced - Actual: {video_path}")

            # 合并所有segments的clips
            all_clips = []
            for segment in segments:
                clips = segment.get('clips', [])
                if clips:
                    all_clips.extend(clips)

            if all_clips:
                # 根据开关：先做小间隙兜底，再合并
                if USE_MERGE_ACTION_CLIPS:
                    preprocessed = fill_small_gaps_before_merge(all_clips)
                    clips_to_use = merge_action_clips(preprocessed)
                else:
                    clips_to_use = all_clips

                video_clips_merged[video_id] = {
                    'original_video_path': original_video_path,
                    'video_path': video_path,
                    'clips': clips_to_use
                }

        # 第三步：提取视频片段并生成CSV
        print("Step 3: Extracting video clips and generating CSV...")
        video_clips_data = []
        processed_count = 0

        for video_id, video_data in video_clips_merged.items():
            video_path = video_data['video_path']
            original_video_path = video_data['original_video_path']
            clips = video_data['clips']

            if not os.path.exists(video_path):
                print(f"Video not found, skipping: {video_path}")
                continue

            # 处理clips，标准化时间格式
            processed_clips = []
            for clip in clips:
                processed_clip = {
                    'start_time': normalize_time_format(clip.get('start_time', '')),
                    'end_time': normalize_time_format(clip.get('end_time', '')),
                    'description': clip.get('event', clip.get('description', '')),
                    'action_id': clip.get('action_id', 'N/A')
                }
                if 'action_desc' in clip and clip['action_desc']:
                    processed_clip['action_desc'] = clip['action_desc']
                processed_clips.append(processed_clip)

            # 提取视频片段
            print(f"Extracting clips from: {video_path} ({len(processed_clips)} clips)")
            extracted_clips = extract_video_clips(video_path, processed_clips, clips_dir)

            # 添加到video_clips_data
            for clip in extracted_clips:
                row = {
                    'video_path': video_path,
                    'original_video_path': original_video_path if original_video_path != video_path else '',
                    'clip_index': clip['clip_index'],
                    'start_time': clip['start_time'],
                    'end_time': clip['end_time'],
                    'event': clip['event'],
                    'action_id': clip.get('action_id', 'N/A')
                }
                if 'action_desc' in clip:
                    row['action_desc'] = clip['action_desc']
                video_clips_data.append(row)

            # 成功处理一个视频，增加计数
            processed_count += 1

        # 保存video_clips.csv
        if video_clips_data:
            clips_df = pd.DataFrame(video_clips_data)
            clips_csv_path = os.path.join(output_dir, "video_clips.csv")
            clips_df.to_csv(clips_csv_path, index=False)
            print(f"Saved video clips to {clips_csv_path}")

            # 生成HTML可视化页面
            generate_html_viewer(clips_df, clips_dir, clips_csv_path)
        else:
            print("No video clips generated")


    def generate_clips_and_html(result_csv_path):
        """生成video_clips.csv和HTML可视化页面"""
        print("Generating video clips and HTML visualization...")

        # 读取结果CSV
        df = pd.read_csv(result_csv_path)

        # 创建video_clips.csv
        video_clips_data = []
        clips_dir = os.path.join(os.path.dirname(result_csv_path), "video_clips")
        os.makedirs(clips_dir, exist_ok=True)

        for _, row in df.iterrows():
            if pd.notna(row.get('parsed_clips')) and row['parsed_clips'] != "[]":
                try:
                    clips = json.loads(row['parsed_clips'])
                    video_path = row['video_path']

                    # 检查路径是否存在，如果不存在且以特定前缀开头，则替换路径
                    original_video_path = video_path
                    if not os.path.exists(video_path):
                        if video_path.startswith("/maindata/data/shared/public/"):
                            new_path = video_path.replace("/maindata/data/shared/public/", "/ai-video-nas-sh-b-2/", 1)
                            if os.path.exists(new_path):
                                video_path = new_path
                                print(f"Path replaced in parser_vis - Original: {original_video_path}")
                                print(f"Path replaced in parser_vis - Actual: {video_path}")
                            else:
                                print(f"ERROR in parser_vis: File not found after path replacement!")
                                print(f"  Original path: {original_video_path}")
                                print(f"  Tried actual path: {new_path}")
                                print(f"  Skipping video clips extraction for this video")
                                continue
                        else:
                            print(f"ERROR in parser_vis: File not found and no path replacement rule matches!")
                            print(f"  Path: {video_path}")
                            print(f"  Skipping video clips extraction for this video")
                            continue

                    if os.path.exists(video_path):
                                # 提取视频片段（使用实际路径）
                                print(f"Extracting clips from: {video_path}")
                                extracted_clips = extract_video_clips(video_path, clips, clips_dir)

                                # 添加到video_clips_data，保存实际使用的路径
                                for clip in extracted_clips:
                                    row = {
                                        'video_path': video_path,  # 保存实际使用的路径
                                        'original_video_path': original_video_path if original_video_path != video_path else '',  # 保留原始路径（如果不同）
                                        'clip_index': clip['clip_index'],
                                        'start_time': clip['start_time'],
                                        'end_time': clip['end_time'],
                                        'event': clip['event'],
                                        'action_id': clip.get('action_id', 'N/A')
                                    }
                                    if 'action_desc' in clip:
                                        row['action_desc'] = clip['action_desc']
                                    video_clips_data.append(row)
                    else:
                        print(f"ERROR in parser_vis: Video file does not exist: {video_path}")

                except Exception as e:
                    print(f"Error processing clips for {row['video_path']}: {e}")
            else:
                # 如果没有parsed_clips，尝试重新解析caption
                if pd.notna(row.get('caption')):
                    try:
                        caption = unescape_csv_content(row['caption'])
                        clips = parse_xml_clips(caption)
                        if clips:
                            if USE_MERGE_ACTION_CLIPS:
                                preprocessed = fill_small_gaps_before_merge(clips)
                                clips_to_use = merge_action_clips(preprocessed)
                            else:
                                clips_to_use = clips
                            original_video_path = row['video_path']
                            video_path = original_video_path

                            # 检查路径是否存在，如果不存在且以特定前缀开头，则替换路径
                            if not os.path.exists(video_path):
                                if video_path.startswith("/maindata/data/shared/public/"):
                                    new_path = video_path.replace("/maindata/data/shared/public/", "/ai-video-nas-sh-b-2/", 1)
                                    if os.path.exists(new_path):
                                        video_path = new_path
                                        print(f"Path replaced in parser_vis - Original: {original_video_path}")
                                        print(f"Path replaced in parser_vis - Actual: {video_path}")
                                    else:
                                        print(f"ERROR in parser_vis: File not found after path replacement!")
                                        print(f"  Original path: {original_video_path}")
                                        print(f"  Tried actual path: {new_path}")
                                        print(f"  Skipping video clips extraction for this video")
                                        continue
                                else:
                                    print(f"ERROR in parser_vis: File not found and no path replacement rule matches!")
                                    print(f"  Path: {video_path}")
                                    print(f"  Skipping video clips extraction for this video")
                                    continue

                            if os.path.exists(video_path):
                                # 提取视频片段（使用实际路径）
                                print(f"Extracting clips from: {video_path}")
                                extracted_clips = extract_video_clips(video_path, clips_to_use, clips_dir)

                                # 添加到video_clips_data，保存实际使用的路径
                                for clip in extracted_clips:
                                    row = {
                                        'video_path': video_path,  # 保存实际使用的路径
                                        'original_video_path': original_video_path if original_video_path != video_path else '',  # 保留原始路径（如果不同）
                                        'clip_index': clip['clip_index'],
                                        'start_time': clip['start_time'],
                                        'end_time': clip['end_time'],
                                        'event': clip['event'],
                                        'action_id': clip.get('action_id', 'N/A')
                                    }
                                    if 'action_desc' in clip:
                                        row['action_desc'] = clip['action_desc']
                                    video_clips_data.append(row)
                            else:
                                print(f"ERROR in parser_vis: Video file does not exist: {video_path}")
                        except Exception as e:
                            print(f"Error reprocessing caption for {row['video_path']}: {e}")

        # 保存video_clips.csv
        if video_clips_data:
            clips_df = pd.DataFrame(video_clips_data)
            clips_csv_path = os.path.join(os.path.dirname(result_csv_path), "video_clips.csv")
            clips_df.to_csv(clips_csv_path, index=False)
            print(f"Saved video clips to {clips_csv_path}")

            # 生成HTML可视化页面
            generate_html_viewer(clips_df, clips_dir, result_csv_path)
        else:
            print("No video clips generated")


    def process_result_csv(result_csv_path, min_duration=5, max_duration=20):
        """处理结果CSV文件，解析clips并生成可视化"""
        print(f"Processing result CSV: {result_csv_path}")

        # 读取结果CSV
        df = pd.read_csv(result_csv_path)

        # 处理每一行
        for idx, row in df.iterrows():
            if pd.notna(row.get('caption')) and row['caption'].strip():
                try:
                    caption = unescape_csv_content(row['caption'])
                    clips = parse_xml_clips(caption)
                    if clips:
                        # 根据开关：先做小间隙兜底，再合并
                        if USE_MERGE_ACTION_CLIPS:
                            preprocessed = fill_small_gaps_before_merge(clips)
                            clips_to_use = merge_action_clips(preprocessed, min_duration, max_duration)
                        else:
                            clips_to_use = clips

                        print(f"Processed {row['video_path']}: {len(clips_to_use)} clips")
                    else:
                        print(f"Processed {row['video_path']}: 0 clips")
                except Exception as e:
                    print(f"Error processing {row['video_path']}: {e}")

        # 不保存更新后的CSV，因为我们不需要添加parsed_clips和num_clips字段
        print(f"Processing completed for CSV: {result_csv_path}")

        # 生成video_clips.csv和HTML可视化
        generate_clips_and_html(result_csv_path)


    parser = argparse.ArgumentParser(description="Parse and visualize video clips from Qwen3-VL results")
    parser.add_argument("--result_csv", help="Path to the result CSV file")
    parser.add_argument("--jsonl", help="Path to the JSONL file (video_clips_scene.jsonl or video_clips_shot.jsonl)")
    parser.add_argument("--output_dir", help="Output directory for video clips and HTML (default: same as input file directory)")
    parser.add_argument("--min_duration", default=5, type=float, help="Minimum duration for clips (seconds)")
    parser.add_argument("--max_duration", default=15, type=float, help="Maximum duration for clips (seconds)")
    parser.add_argument("--limit", type=int, help="Limit the number of entries to process (e.g., --limit 100 for first 100 entries)")

    args = parser.parse_args()

    # 检查输入文件参数
    if not args.result_csv and not args.jsonl:
        print("Error: Must provide either --result_csv or --jsonl")
        parser.print_help()
        exit(1)

    if args.result_csv and args.jsonl:
        print("Error: Cannot specify both --result_csv and --jsonl")
        parser.print_help()
        exit(1)

    # 处理JSONL文件
    if args.jsonl:
        if not os.path.exists(args.jsonl):
            print(f"Error: JSONL file not found: {args.jsonl}")
            exit(1)
        process_jsonl_file(args.jsonl, args.output_dir, args.limit)
    # 处理CSV文件
    elif args.result_csv:
        if not os.path.exists(args.result_csv):
            print(f"Error: Result CSV file not found: {args.result_csv}")
            exit(1)
        process_result_csv(args.result_csv, args.min_duration, args.max_duration)
