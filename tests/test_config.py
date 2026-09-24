import os
import json
from src.config import AppConfig


def test_default_config():
    config = AppConfig()
    assert config.camera_index == 0
    assert config.frame_width == 640
    assert config.frame_height == 480
    assert config.smoothing_factor == 5.0
    assert config.pinch_threshold == 38.0


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
