from src.mouse_controller import MouseController


def test_mouse_controller_init():
    mouse = MouseController(
        screen_size=(1920, 1080),
        frame_size=(640, 480),
        frame_margin=100,
        smoothing_factor=4.0,
        deadzone=2.0
    )
    assert mouse.screen_w == 1920
    assert mouse.screen_h == 1080
    assert mouse.smoothing == 4.0


def test_map_coordinates_center():
    mouse = MouseController(
        screen_size=(1920, 1080),
        frame_size=(640, 480),
        frame_margin=100,
        smoothing_factor=1.0  # Immediate, no lag
    )
    # Center of active region: x = 320, y = 240
    sx, sy = mouse.map_coordinates(320, 240)
    assert abs(sx - 960) <= 2
    assert abs(sy - 540) <= 2


def test_map_coordinates_boundary_clamping():
    mouse = MouseController(
        screen_size=(1000, 1000),
        frame_size=(500, 500),
        frame_margin=50,
        smoothing_factor=1.0
    )
    # Out of bounds left/top -> clamped to edge
    sx, sy = mouse.map_coordinates(0, 0)
    assert sx == 0
    assert sy == 0

    # Out of bounds right/bottom
    sx, sy = mouse.map_coordinates(600, 600)
    assert sx == 1000
    assert sy == 1000


def test_mouse_drag_state():
    mouse = MouseController(screen_size=(800, 600))
    assert not mouse.is_dragging
    mouse.start_drag()
    assert mouse.is_dragging
    mouse.end_drag()
    assert not mouse.is_dragging
