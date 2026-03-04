"""
T009 [P] [US1] Test utils module imports
Tests that all utility modules can be imported correctly
"""
import pytest


def test_import_time_utils():
    """Test that time_utils module can be imported"""
    from src.utils import time_utils
    assert time_utils is not None


def test_import_json_utils():
    """Test that json_utils module can be imported"""
    from src.utils import json_utils
    assert json_utils is not None


def test_import_xml_parser():
    """Test that xml_parser module can be imported"""
    from src.utils import xml_parser
    assert xml_parser is not None


def test_import_video_utils():
    """Test that video_utils module can be imported"""
    from src.utils import video_utils
    assert video_utils is not None


def test_time_utils_functions():
    """Test that time_utils has expected functions"""
    from src.utils import time_utils
    assert hasattr(time_utils, 'time_to_seconds')
    assert hasattr(time_utils, 'seconds_to_time')
    assert hasattr(time_utils, 'frame_to_seconds')


def test_xml_parser_functions():
    """Test that xml_parser has expected functions"""
    from src.utils import xml_parser
    assert hasattr(xml_parser, 'parse_xml_clips')


def test_json_utils_functions():
    """Test that json_utils has expected functions"""
    from src.utils import json_utils
    assert hasattr(json_utils, 'fast_json_dumps')


def test_video_utils_functions():
    """Test that video_utils has expected functions"""
    from src.utils import video_utils
    assert hasattr(video_utils, 'get_video_fps_from_clips')
