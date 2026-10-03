import json
import pytest
from src.config import AppConfig


def test_default_config():
    config = AppConfig()
    assert config.camera_index == 0
    assert config.frame_width == 640
    assert config.frame_height == 480
    assert config.smoothing_factor == 5.0
    assert config.pinch_threshold == 38.0
    assert config.enable_adaptive_smoothing is True
    assert config.enable_analytics is True


def test_config_save_and_load(tmp_path):
    config_file = str(tmp_path / "test_config.json")
    original = AppConfig(
        camera_index=1,
        frame_margin=120,
        smoothing_factor=7.5,
        pinch_threshold=42.0
    )
    original.save(config_file)

    loaded = AppConfig.load(config_file)
    assert loaded.camera_index == 1
    assert loaded.frame_margin == 120
    assert loaded.smoothing_factor == 7.5
    assert loaded.pinch_threshold == 42.0


def test_config_unknown_fields_filtering(tmp_path):
    config_file = str(tmp_path / "extra_fields_config.json")
    data = {
        "camera_index": 2,
        "smoothing_factor": 6.0,
        "unknown_parameter": "should_be_ignored",
        "another_extra_key": 999
    }
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(data, f)

    loaded = AppConfig.load(config_file)
    assert loaded.camera_index == 2
    assert loaded.smoothing_factor == 6.0
    assert not hasattr(loaded, "unknown_parameter")


def test_config_validation_and_clamping():
    config = AppConfig(
        camera_index=-1,
        detection_confidence=1.5,
        tracking_confidence=-0.5,
        frame_width=50,
        smoothing_factor=0.5,
        primary_color=[0, 255, 128]
    )
    validated = config.validate()
    assert validated.camera_index == 0
    assert validated.detection_confidence == 1.0
    assert validated.tracking_confidence == 0.0
    assert validated.frame_width == 100
    assert validated.smoothing_factor == 1.0
    assert isinstance(validated.primary_color, tuple)
    assert validated.primary_color == (0, 255, 128)


def test_config_invalid_json_fallback(tmp_path):
    corrupt_file = str(tmp_path / "corrupt.json")
    with open(corrupt_file, "w", encoding="utf-8") as f:
        f.write("{ invalid json content }")

    loaded = AppConfig.load(corrupt_file)
    assert loaded.camera_index == 0
    assert loaded.frame_width == 640
