"""Core package."""

# Note: Modules are not imported here by default to avoid hard dependencies
# Import them directly as needed, e.g.:
# from src.core.scene_detector import TransNetWorker
# from src.core.result_merger import merge_clips_by_duration

__all__ = [
    'scene_detector',
    'action_recognizer',
    'video_processor',
    'result_merger',
    'visualizer',
]

