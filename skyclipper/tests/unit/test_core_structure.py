"""
T010 [P] [US1] Test core module structure
Tests that all core modules exist and can be imported
"""
import pytest


def test_import_scene_detector():
    """Test that scene_detector module can be imported"""
    import src.core.scene_detector as scene_detector
    assert scene_detector is not None


def test_import_action_recognizer():
    """Test that action_recognizer module can be imported (with optional deps)"""
    try:
        import src.core.action_recognizer as action_recognizer
        assert action_recognizer is not None
    except ImportError:
        pytest.skip("Optional dependencies not available")


def test_import_video_processor():
    """Test that video_processor module can be imported (with optional deps)"""
    try:
        import src.core.video_processor as video_processor
        assert video_processor is not None
    except ImportError:
        pytest.skip("Optional dependencies not available")


def test_import_result_merger():
    """Test that result_merger module can be imported"""
    import src.core.result_merger as result_merger
    assert result_merger is not None


def test_import_visualizer():
    """Test that visualizer module can be imported"""
    import src.core.visualizer as visualizer
    assert visualizer is not None


def test_scene_detector_has_transnet_worker():
    """Test that scene_detector has TransNetWorker class"""
    import src.core.scene_detector as scene_detector
    assert hasattr(scene_detector, 'TransNetWorker')


def test_action_recognizer_has_inference_logic():
    """Test that action_recognizer has expected functions/classes"""
    try:
        import src.core.action_recognizer as action_recognizer
        # Should have Qwen3-VL related inference logic
        assert (hasattr(action_recognizer, 'prepareVideoData') or
                hasattr(action_recognizer, 'prepare_video_data'))
    except ImportError:
        pytest.skip("Optional dependencies not available")


def test_video_processor_has_pipeline():
    """Test that video_processor has pipeline orchestration"""
    try:
        import src.core.video_processor as video_processor
        assert (hasattr(video_processor, 'processVideoPipeline') or
                hasattr(video_processor, 'process_video_pipeline'))
    except ImportError:
        pytest.skip("Optional dependencies not available")


def test_result_merger_has_merge_logic():
    """Test that result_merger has merging functions"""
    import src.core.result_merger as result_merger
    assert hasattr(result_merger, 'mergeClipsByDuration') or hasattr(result_merger, 'merge_clips_by_duration')
    assert hasattr(result_merger, 'processSingleNodeFile') or hasattr(result_merger, 'process_single_node_file')
    assert hasattr(result_merger, 'mergeTempFiles') or hasattr(result_merger, 'merge_temp_files')


def test_visualizer_has_html_generation():
    """Test that visualizer has HTML generation logic"""
    import src.core.visualizer as visualizer
    assert hasattr(visualizer, 'generateHtml') or hasattr(visualizer, 'generate_html')
