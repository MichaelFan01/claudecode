#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for xml_parser module.
"""

import pytest
from src.utils.xml_parser import (
    parseXmlClips,
    extractXmlFromText,
    hasXmlContent,
    cleanXmlText,
    parse_xml_clips,
    extract_xml_from_text,
    has_xml_content,
    clean_xml_text,
)


class TestParseXmlClips:
    """Tests for parseXmlClips function."""

    def test_basic_parse(self):
        """Test basic XML parsing."""
        xml = """
<clip>
    <time>00:00:00.000-00:00:05.000</time>
    <action>1</action>
    This is a test event.
</clip>
"""
        clips = parseXmlClips(xml)
        assert len(clips) == 1
        assert clips[0]['start_time'] == "00:00:00.000"
        assert clips[0]['end_time'] == "00:00:05.000"
        assert clips[0]['action_id'] == 1
        assert clips[0]['event'] == "This is a test event."

    def test_with_action_desc(self):
        """Test parsing with optional action_desc field."""
        xml = """
<clip>
    <time>00:00:00.000-00:00:05.000</time>
    <action>1</action>
    <action_desc>Running</action_desc>
    This is a test event.
</clip>
"""
        clips = parseXmlClips(xml)
        assert len(clips) == 1
        assert clips[0]['action_desc'] == "Running"

    def test_with_markdown(self):
        """Test parsing XML wrapped in markdown code blocks."""
        xml = """```xml
<clip>
    <time>00:00:00.000-00:00:05.000</time>
    <action>1</action>
    Test
</clip>
```
"""
        clips = parseXmlClips(xml)
        assert len(clips) == 1
        assert clips[0]['event'] == "Test"

    def test_multiple_clips(self):
        """Test parsing multiple clips."""
        xml = """
<clip>
    <time>00:00:00.000-00:00:05.000</time>
    <action>1</action>
    First event
</clip>
<clip>
    <time>00:00:05.000-00:00:10.000</time>
    <action>2</action>
    Second event
</clip>
"""
        clips = parseXmlClips(xml)
        assert len(clips) == 2
        assert clips[0]['action_id'] == 1
        assert clips[1]['action_id'] == 2


class TestExtractXmlFromText:
    """Tests for extractXmlFromText function."""

    def test_extract_markdown_xml(self):
        """Test extracting XML from markdown code blocks."""
        text = """Here's some XML:
```xml
<clip>Test</clip>
```
That was it.
"""
        xml = extractXmlFromText(text)
        assert "<clip>Test</clip>" in xml

    def test_extract_clip_elements(self):
        """Test extracting clip elements from mixed text."""
        text = "Here's a clip: <clip>Test</clip> - that's all."
        xml = extractXmlFromText(text)
        assert "<clip>Test</clip>" in xml


class TestHasXmlContent:
    """Tests for hasXmlContent function."""

    def test_has_xml(self):
        """Test detecting XML content."""
        assert hasXmlContent("<clip>Test</clip>") is True
        assert hasXmlContent("No tags here") is False


class TestCleanXmlText:
    """Tests for cleanXmlText function."""

    def test_fix_entities(self):
        """Test fixing XML entities."""
        assert cleanXmlText("&lt;clip&gt;") == "<clip>"
        assert cleanXmlText("&amp;") == "&"


class TestSnakeCaseAliases:
    """Tests for snake_case alias functions."""

    def test_aliases_exist(self):
        """Test that snake_case aliases exist and work."""
        xml = """
<clip>
    <time>00:00:00.000-00:00:05.000</time>
    <action>1</action>
    Test
</clip>
"""
        clips1 = parseXmlClips(xml)
        clips2 = parse_xml_clips(xml)
        assert len(clips1) == len(clips2) == 1

        # Test other aliases exist
        assert extract_xml_from_text is not None
        assert has_xml_content is not None
        assert clean_xml_text is not None
