#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for json_utils module.
"""

import os
import tempfile
import pytest
from src.utils.json_utils import (
    fastJsonDumps,
    fastJsonLoads,
    loadJsonlFile,
    saveJsonlFile,
    safeJsonLoads,
    mergeJsonObjects,
    getNestedValue,
    jsonPrettyPrint,
    fast_json_dumps,
    fast_json_loads,
    load_jsonl_file,
    save_jsonl_file,
    safe_json_loads,
    merge_json_objects,
    get_nested_value,
    json_pretty_print,
)


class TestFastJsonDumps:
    """Tests for fastJsonDumps function."""

    def test_basic_serialization(self):
        """Test basic JSON serialization."""
        obj = {"key": "value", "number": 42}
        json_str = fastJsonDumps(obj)
        assert "key" in json_str
        assert "value" in json_str
        assert "42" in json_str

    def test_unicode_handling(self):
        """Test that unicode characters are handled correctly."""
        obj = {"text": "测试 こんにちは 🌍"}
        json_str = fastJsonDumps(obj)
        # Should not escape unicode by default
        assert "测试" in json_str or "\\u6d4b\\u8bd5" in json_str


class TestFastJsonLoads:
    """Tests for fastJsonLoads function."""

    def test_basic_deserialization(self):
        """Test basic JSON deserialization."""
        json_str = '{"key": "value", "number": 42}'
        obj = fastJsonLoads(json_str)
        assert obj["key"] == "value"
        assert obj["number"] == 42


class TestSafeJsonLoads:
    """Tests for safeJsonLoads function."""

    def test_valid_json(self):
        """Test with valid JSON."""
        result = safeJsonLoads('{"key": "value"}', default={})
        assert result == {"key": "value"}

    def test_invalid_json_with_default(self):
        """Test with invalid JSON returns default."""
        result = safeJsonLoads('not valid json', default={"error": True})
        assert result == {"error": True}


class TestMergeJsonObjects:
    """Tests for mergeJsonObjects function."""

    def test_shallow_merge(self):
        """Test shallow merge of objects."""
        obj1 = {"a": 1, "b": 2}
        obj2 = {"b": 3, "c": 4}
        merged = mergeJsonObjects(obj1, obj2)
        assert merged == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge(self):
        """Test deep merge of nested objects."""
        obj1 = {"nested": {"a": 1}}
        obj2 = {"nested": {"b": 2}}
        merged = mergeJsonObjects(obj1, obj2, deep=True)
        assert merged == {"nested": {"a": 1, "b": 2}}


class TestGetNestedValue:
    """Tests for getNestedValue function."""

    def test_get_nested_value(self):
        """Test getting a nested value."""
        obj = {"video_meta": {"fps": 30.0, "duration": 100.0}}
        fps = getNestedValue(obj, "video_meta.fps")
        assert fps == 30.0

    def test_nonexistent_path_with_default(self):
        """Test non-existent path returns default."""
        obj = {"video_meta": {}}
        value = getNestedValue(obj, "video_meta.nonexistent", default=0.0)
        assert value == 0.0


class TestJsonPrettyPrint:
    """Tests for jsonPrettyPrint function."""

    def test_pretty_print(self):
        """Test pretty printing produces formatted output."""
        obj = {"key": "value", "list": [1, 2, 3]}
        pretty = jsonPrettyPrint(obj, indent=2)
        assert "\n" in pretty  # Should have newlines
        assert "  " in pretty  # Should have indentation


class TestJsonlFileOperations:
    """Tests for JSONL file operations."""

    def test_save_and_load_jsonl(self):
        """Test saving and loading JSONL files."""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            temp_path = f.name

        try:
            # Save
            saveJsonlFile(data, temp_path)

            # Load
            loaded = loadJsonlFile(temp_path)
            assert len(loaded) == 3
            assert loaded[0]["id"] == 1
            assert loaded[2]["id"] == 3
        finally:
            os.unlink(temp_path)


class TestSnakeCaseAliases:
    """Tests for snake_case alias functions."""

    def test_aliases_exist_and_work(self):
        """Test that snake_case aliases exist and work."""
        obj = {"key": "value"}
        json_str = fastJsonDumps(obj)
        json_str2 = fast_json_dumps(obj)
        assert json_str == json_str2

        loaded1 = fastJsonLoads(json_str)
        loaded2 = fast_json_loads(json_str)
        assert loaded1 == loaded2

        # Test other aliases exist
        assert safe_json_loads is not None
        assert merge_json_objects is not None
        assert get_nested_value is not None
        assert json_pretty_print is not None
        assert load_jsonl_file is not None
        assert save_jsonl_file is not None
