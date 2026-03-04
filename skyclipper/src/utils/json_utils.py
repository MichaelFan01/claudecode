#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON utility functions for fast serialization/deserialization.

This module provides JSON handling with optional orjson acceleration
and helper functions for common JSON operations.
"""

import json
from pathlib import Path

# Fast JSON parsing with orjson fallback
try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False


def fastJsonDumps(obj):
    """
    Fast JSON serialization with orjson fallback.

    Args:
        obj: Object to serialize to JSON

    Returns:
        str: JSON string
    """
    if HAS_ORJSON:
        return orjson.dumps(obj).decode('utf-8')
    return json.dumps(obj, ensure_ascii=False)


def fastJsonLoads(jsonStr):
    """
    Fast JSON deserialization with orjson fallback.

    Args:
        jsonStr: JSON string to parse

    Returns:
        Any: Parsed JSON object
    """
    if HAS_ORJSON:
        return orjson.loads(jsonStr)
    return json.loads(jsonStr)


def loadJsonlFile(filePath):
    """
    Load a JSONL file (one JSON object per line).

    Args:
        filePath: Path to JSONL file

    Returns:
        list: List of parsed JSON objects
    """
    results = []
    with open(filePath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    results.append(fastJsonLoads(line))
                except json.JSONDecodeError:
                    continue
    return results


def saveJsonlFile(data, filePath, append=False):
    """
    Save data to a JSONL file.

    Args:
        data: List of objects to save
        filePath: Output file path
        append: If True, append to existing file instead of overwriting
    """
    mode = 'a' if append else 'w'
    with open(filePath, mode, encoding='utf-8') as f:
        for item in data:
            f.write(fastJsonDumps(item) + '\n')


def safeJsonLoads(jsonStr, default=None):
    """
    Safely parse JSON, returning a default on failure.

    Args:
        jsonStr: JSON string to parse
        default: Value to return on parse failure

    Returns:
        Any: Parsed JSON object or default value
    """
    try:
        return fastJsonLoads(jsonStr)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default


def mergeJsonObjects(*objects, deep=False):
    """
    Merge multiple JSON objects.

    Args:
        *objects: Objects to merge
        deep: If True, perform deep merge for nested dicts

    Returns:
        dict: Merged object
    """
    if not objects:
        return {}

    result = {}
    for obj in objects:
        if not isinstance(obj, dict):
            continue

        if deep:
            result = _deepMerge(result, obj)
        else:
            result.update(obj)

    return result


def _deepMerge(dest, source):
    """Deep merge helper function."""
    for key, value in source.items():
        if key in dest and isinstance(dest[key], dict) and isinstance(value, dict):
            dest[key] = _deepMerge(dest[key], value)
        else:
            dest[key] = value
    return dest


def getNestedValue(obj, keyPath, default=None):
    """
    Get a nested value from a JSON object using dot notation.

    Args:
        obj: JSON object
        keyPath: Dot-separated key path (e.g., "video_meta.fps")
        default: Default value if path not found

    Returns:
        Any: Value at path or default
    """
    keys = keyPath.split('.')
    current = obj

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current


def jsonPrettyPrint(obj, indent=2):
    """
    Pretty print JSON object with proper formatting.

    Args:
        obj: Object to print
        indent: Indentation level

    Returns:
        str: Pretty printed JSON string
    """
    return json.dumps(obj, ensure_ascii=False, indent=indent, sort_keys=True)


# Snake_case aliases for backward compatibility
fast_json_dumps = fastJsonDumps
fast_json_loads = fastJsonLoads
load_jsonl_file = loadJsonlFile
save_jsonl_file = saveJsonlFile
safe_json_loads = safeJsonLoads
merge_json_objects = mergeJsonObjects
get_nested_value = getNestedValue
json_pretty_print = jsonPrettyPrint
