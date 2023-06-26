from argparse import ArgumentParser, FileType
from os import get_terminal_size
from sys import stdout
from time import monotonic, sleep
from typing import Generator

from cursor import hide as hide_cursor
from cursor import show as show_cursor
from cv2 import VideoCapture
from ffmpeg import probe
from numpy import asarray, ndarray
from PIL import Image
from pydub import AudioSegment
from simpleaudio import play_buffer

_RESET_FG = "\x1b[0m"


def _resize_image(image: ndarray, window_size: tuple[int, int]) -> ndarray:
    return asarray(Image.fromarray(image).resize(window_size))


def _read_video_frames(
    video_path: str, size: tuple[int, int]
) -> Generator[ndarray, None, None]:
    vidcap = VideoCapture(video_path)
    while True:
        sucess, image = vidcap.read()
        if not sucess:
            break

        yield _resize_image(image, size)


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


def view_video(video_path: str):
    audio_segment = AudioSegment.from_file(video_path)

    info = probe(video_path)
    duration: float = float(info["streams"][0]["duration"])
    frames_number: float = float(info["streams"][0]["nb_frames"])
    frame_duration: int = duration / frames_number

    terminal_size = get_terminal_size()
    video_size = _get_video_size(
        tuple(map(int, info["streams"][0]["display_aspect_ratio"].split(":"))),
        (int(terminal_size.columns / 2), terminal_size.lines - 1),
    )

    print(chr(27) + "[2J", end="")
    hide_cursor()
    frames_generator = _read_video_frames(
        video_path, size=(video_size[0] * 2, video_size[1])
    )
    try:
        start_time = monotonic()
        playback = play_buffer(
            audio_segment.raw_data,
            num_channels=audio_segment.channels,
            bytes_per_sample=audio_segment.sample_width,
            sample_rate=audio_segment.frame_rate,
        )

        frame_number = 0
        while True:
            delta = (frame_duration * frame_number) - (monotonic() - start_time)
            if delta > 0:
                sleep(delta)

            frame = next(frames_generator)
            frame_number += 1

            if delta < 0:
                continue

            height, width, _ = frame.shape
            stdout.write(f"\x1b[{height + 1}A")
            for height_idx in range(height):
                for width_idx in range(width):
                    red, green, blue = frame[height_idx][width_idx]
                    stdout.write(f"\x1b[48;2;{blue};{green};{red}m ")
                stdout.write(_RESET_FG + "\n")

            stdout.write(_format_time(monotonic() - start_time) + "\n")
            stdout.flush()
    except StopIteration:
        pass
    finally:
        playback.stop()
        show_cursor()


def _parse_args():
    parser = ArgumentParser()
    parser.add_argument("--mp4-file", type=FileType(), required=True)

    return parser.parse_args()


def main():
    args = _parse_args()

    try:
        view_video(args.mp4_file.name)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
