#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML parsing utilities for clip extraction.

This module provides functions for parsing XML-formatted clip data
from LLM outputs.
"""

import re
from .time_utils import timeToSeconds, parseTimeRange


def parseXmlClips(xmlText):
    """
    Parse XML format clip output, supporting optional <action_desc> field.

    Extracts clip information from XML text, handling markdown code blocks
    and optional action description fields.

    Args:
        xmlText: XML text string, may include ```xml markdown markers

    Returns:
        list: List of clip dictionaries with keys:
            - start_time: Start time string
            - end_time: End time string
            - action_id: Action ID integer
            - event: Event description
            - action_desc: Optional action description (if present)
    """
    clips = []

    # Remove ```xml markers
    if '```xml' in xmlText:
        xmlText = xmlText.split('```xml')[1]
    if '```' in xmlText:
        xmlText = xmlText.split('```')[0]

    # Extract clip info with regex, supporting optional <action_desc>
    clipPattern = r'<clip>\s*<time>(.*?)</time>\s*<action>(.*?)</action>\s*(?:<action_desc>(.*?)</action_desc>\s*)?(.*?)\s*</clip>'
    matches = re.findall(clipPattern, xmlText, re.DOTALL)

    for match in matches:
        timeStr, actionId, actionDesc, description = match
        timeStr = timeStr.strip()
        description = description.strip()
        actionDesc = (actionDesc or '').strip()

        # Parse time range
        if '-' not in timeStr:
            continue

        startTime, endTime = timeStr.split('-', 1)
        startTime = startTime.strip()
        endTime = endTime.strip()

        # Validate time format
        try:
            timeToSeconds(startTime)
            timeToSeconds(endTime)
        except (ValueError, IndexError):
            continue

        clipItem = {
            'start_time': startTime,
            'end_time': endTime,
            'action_id': int(actionId.strip()),
            'event': description
        }
        if actionDesc:
            clipItem['action_desc'] = actionDesc
        clips.append(clipItem)

    return clips


def extractXmlFromText(text):
    """
    Extract XML content from mixed text.

    Finds and extracts XML blocks that might be embedded in other text.

    Args:
        text: Text that may contain XML

    Returns:
        str: Extracted XML content, or empty string if none found
    """
    # Try to find content between ```xml and ```
    xmlMatch = re.search(r'```xml\s*(.*?)\s*```', text, re.DOTALL)
    if xmlMatch:
        return xmlMatch.group(1)

    # Try to find any <clip> elements
    clipMatch = re.search(r'(<clip>.*?</clip>)', text, re.DOTALL)
    if clipMatch:
        return clipMatch.group(1)

    return text


def hasXmlContent(text):
    """
    Check if text contains XML clip content.

    Args:
        text: Text to check

    Returns:
        bool: True if text appears to contain XML clips
    """
    return '<clip>' in text and '</clip>' in text


def cleanXmlText(xmlText):
    """
    Clean up XML text by removing common formatting issues.

    Args:
        xmlText: Raw XML text

    Returns:
        str: Cleaned XML text
    """
    # Remove common escaping issues
    xmlText = xmlText.replace('&lt;', '<').replace('&gt;', '>')
    xmlText = xmlText.replace('&amp;', '&')

    # Fix common malformed XML patterns
    xmlText = re.sub(r'</?s*>', '', xmlText)  # Remove empty tags

    return xmlText


# Snake_case aliases for backward compatibility
parse_xml_clips = parseXmlClips
extract_xml_from_text = extractXmlFromText
has_xml_content = hasXmlContent
clean_xml_text = cleanXmlText
