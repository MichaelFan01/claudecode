#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for result_merger module.
"""

import pytest
from src.core.result_merger import (
    splitLongClipWithTransnet,
    splitLongClipHard,
    mergeClipsByDuration,
    split_long_clip_with_transnet,
    split_long_clip_hard,
    merge_clips_by_duration,
)


class TestSplitLongClipHard:
    """Tests for splitLongClipHard function."""

    def test_short_clip_no_split(self):
        """Test that a short clip is not split."""
        clip = {
            'start_time': '00:00:00.000',
            'end_time': '00:00:05.000',
            'event': 'Test event'
        }
        result = splitLongClipHard(clip, videoFps=30.0, maxDurationSeconds=10)
        assert len(result) == 1
        assert result[0] == clip

    def test_long_clip_split(self):
        """Test that a long clip is split into multiple parts."""
        clip = {
            'start_time': '00:00:00.000',
            'end_time': '00:00:25.000',
            'event': 'Test event',
            'action_id': 1
        }
        result = splitLongClipHard(clip, videoFps=30.0, maxDurationSeconds=10)
        assert len(result) == 3
        assert result[0]['start_time'] == '00:00:00.000'
        assert result[0]['end_time'] == '00:00:10.000'
        assert result[1]['start_time'] == '00:00:10.000'
        assert result[1]['end_time'] == '00:00:20.000'
        assert result[2]['start_time'] == '00:00:20.000'
        assert result[2]['end_time'] == '00:00:25.000'


class TestMergeClipsByDuration:
    """Tests for mergeClipsByDuration function."""

    def test_empty_clips_list(self):
        """Test that an empty list returns empty."""
        result = mergeClipsByDuration([])
        assert result == []

    def test_single_clip_no_merge(self):
        """Test that a single clip is returned unchanged."""
        clips = [{
            'start_time': '00:00:00.000',
            'end_time': '00:00:05.000',
            'event': 'Test event',
            'action_id': 1
        }]
        result = mergeClipsByDuration(clips, videoFps=30.0)
        assert len(result) == 1
        assert result[0]['event'] == 'Test event'

    def test_adjacent_same_action_merged(self):
        """Test that adjacent clips with same action are merged."""
        clips = [
            {
                'start_time': '00:00:00.000',
                'end_time': '00:00:05.000',
                'event': 'First part',
                'action_id': 1
            },
            {
                'start_time': '00:00:05.000',
                'end_time': '00:00:10.000',
                'event': 'Second part',
                'action_id': 1
            }
        ]
        result = mergeClipsByDuration(clips, videoFps=30.0, maxDurationSeconds=15)
        assert len(result) == 1
        assert result[0]['start_time'] == '00:00:00.000'
        assert result[0]['end_time'] == '00:00:10.000'

    def test_different_actions_not_merged(self):
        """Test that clips with different actions are not merged."""
        clips = [
            {
                'start_time': '00:00:00.000',
                'end_time': '00:00:05.000',
                'event': 'Action 1',
                'action_id': 1
            },
            {
                'start_time': '00:00:05.000',
                'end_time': '00:00:10.000',
                'event': 'Action 2',
                'action_id': 2
            }
        ]
        result = mergeClipsByDuration(clips, videoFps=30.0)
        assert len(result) == 2


class TestSnakeCaseAliases:
    """Tests for snake_case alias functions."""

    def test_aliases_exist(self):
        """Test that snake_case aliases exist and are the same as original."""
        assert split_long_clip_with_transnet is splitLongClipWithTransnet
        assert split_long_clip_hard is splitLongClipHard
        assert merge_clips_by_duration is mergeClipsByDuration
