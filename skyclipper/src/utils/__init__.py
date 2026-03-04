"""Utilities package."""

# Utility modules (kebab-case filenames)
from . import time_utils
from . import xml_parser
from . import json_utils
from . import video_utils

# Aliases for backward compatibility (kebab-case to snake_case)
# Note: The actual files are in kebab-case, but Python imports use snake_case
timeUtils = time_utils
xmlParser = xml_parser
jsonUtils = json_utils
videoUtils = video_utils

__all__ = [
    'time_utils',
    'xml_parser',
    'json_utils',
    'video_utils',
    'timeUtils',
    'xmlParser',
    'jsonUtils',
    'videoUtils',
]
