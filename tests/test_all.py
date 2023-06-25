import pytest

from mp_terminal.main import _get_video_size


@pytest.mark.parametrize(
    "display_ratio,terminal_size,expects",
    [
        [(16, 9), (1280, 720), (1280, 720)],
        [(16, 9), (1300, 800), (1296, 729)],
        [(16, 9), (243, 62), (96, 54)],
    ],
)
def test_get_video_size(display_ratio, terminal_size, expects):
    result = _get_video_size(display_ratio, terminal_size)

    width, height = result
    width_ratio, height_ratio = display_ratio

    assert width / width_ratio == height / height_ratio
    assert result == expects
    assert width > height
