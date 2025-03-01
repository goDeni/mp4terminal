from functools import cached_property
from time import monotonic, sleep
from typing import TextIO, Tuple
from os import get_terminal_size

from cursor import hide as cursor_hide
from cursor import show as cursor_show
from cv2 import INTER_AREA, resize
from numpy import ndarray

_RESET_FG = "\x1b[0m"
_CLEAR_TERMINAL = chr(27) + "[2J"


class TerminalPlayer:
    def __init__(
        self,
        stream: TextIO,
        resolution: Tuple[int, int],
        fps: float,
        duration: float,
    ):
        self._stream = stream
        self._resolution = resolution
        self._fps = fps
        self._duration = duration

        self._width, self._height = 0, 0
        self._update_resolution()

        self._frames_count: int = 0
        self._start_time: float = 0.0

    def _update_resolution(self):
        terminal_size = get_terminal_size()
        resolution = _get_video_size(
            self._resolution,
            (terminal_size.columns, terminal_size.lines),
        )
        self._width, self._height = resolution

    @property
    def _video_resolution(self) -> Tuple[int, int]:
        return (self._video_width, self._video_height)

    @cached_property
    def _frame_duration(self) -> float:
        return 1 / self._fps

    @property
    def _video_height(self) -> int:
        return self._height - 1

    @property
    def _video_width(self) -> int:
        return self._width * 2

    def render_frame(self, frame: ndarray):
        self._update_resolution()
        delta = (self._frame_duration * self._frames_count) - (
            monotonic() - self._start_time
        )
        if delta > 0:
            sleep(delta)

        self._frames_count += 1
        if delta < 0:
            return

        self._stream.write(f"\x1b[{self._video_height + 1}A")

        for line in _resize_frame(frame, self._video_resolution):
            for pixel in line:
                blue, green, red = pixel
                self._stream.write(f"\x1b[48;2;{red};{green};{blue}m ")
            self._stream.write("\n")

        self._stream.write(_RESET_FG + self._get_status_line() + "\n")
        self._stream.flush()

    def _get_status_line(self) -> str:
        line = f"{_format_time(monotonic() - self._start_time)}/{_format_time(self._duration)}".center(
            self._video_width
        ).rstrip()
        line += f"FPS: {self._fps:.2f}".rjust(self._video_width - len(line), " ")

        return line

    def start(self):
        self._start_time = monotonic()
        cursor_hide(self._stream)
        self._stream.write(_CLEAR_TERMINAL)

    def reset(self, clear_terminal: bool = True):
        self._stream.write(_RESET_FG)
        cursor_show(self._stream)
        if clear_terminal:
            self._stream.write(_CLEAR_TERMINAL)


def _resize_frame(frame: ndarray, window_size: tuple[int, int]) -> ndarray:
    return resize(frame, window_size, interpolation=INTER_AREA)


def _format_time(seconds: float):
    minutes = int(seconds / 60)
    if minutes:
        seconds -= minutes * 60

    return f"{minutes:-02}:{int(seconds):-02}"


def _get_video_size(display_ratio: tuple[int, int], terminal_size: tuple[int, int]):
    width_ratio, height_ratio = display_ratio
    width, height = terminal_size

    while width and height:
        while width > 0 and width % width_ratio != 0:
            width -= 1

        while height > 0 and height % height_ratio != 0:
            height -= 1

        if width / width_ratio == height / height_ratio:
            return width, height

        if width / width_ratio > height / height_ratio:
            width -= 1
        else:
            height -= 1

    return terminal_size
