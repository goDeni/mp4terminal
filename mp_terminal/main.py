from argparse import ArgumentParser, FileType
from os import get_terminal_size
from sys import stdout

from cv2 import VideoCapture
from pydub import AudioSegment
from simpleaudio import play_buffer

from mp_terminal.terminal_player import TerminalPlayer
from mp_terminal.video_meta import get_video_meta


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
    meta = get_video_meta(video_path)

    terminal_size = get_terminal_size()
    resolution = _get_video_size(
        meta.resolution,
        (terminal_size.columns, terminal_size.lines),
    )
    vidcap = VideoCapture(video_path)

    terminal_player = TerminalPlayer(stdout, resolution, meta.fps, meta.duration)
    playback = play_buffer(
        audio_segment.raw_data,
        num_channels=audio_segment.channels,
        bytes_per_sample=audio_segment.sample_width,
        sample_rate=audio_segment.frame_rate,
    )
    terminal_player.start()
    try:
        while True:
            sucess, frame = vidcap.read()
            if not sucess:
                break

            terminal_player.render_frame(frame)
    except KeyboardInterrupt:
        terminal_player.reset(True)
        raise
    except:
        terminal_player.reset(False)
        raise
    else:
        terminal_player.reset(True)
    finally:
        playback.stop()


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
