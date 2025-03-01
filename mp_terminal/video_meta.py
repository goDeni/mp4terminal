from dataclasses import dataclass
from typing import Any, Dict

from ffmpeg import probe


@dataclass
class VideoMeta:
    duration: float
    frames_number: int
    resolution: tuple[int, int]
    fps: float


def _get_duration(video_stream_info: Dict[str, Any]) -> float:
    if (duration := video_stream_info.get("duration")) is not None:
        return float(duration)

    if (tags := video_stream_info.get("tags")) is not None:
        if (duration := tags.get("DURATION")) is not None:
            # 00:22:46.006000000
            hours, minutes, seconds = duration.split(":", maxsplit=3)
            return (int(hours) * 60 + int(minutes)) * 60 + float(seconds)
    raise ValueError("Unable to find video duration")


def _get_frames_number(video_stream_info: Dict[str, Any]) -> int:
    if (nb_frames := video_stream_info.get("nb_frames")) is not None:
        return int(nb_frames)

    if (tags := video_stream_info.get("tags")) is not None:
        if (nb_frames := tags.get("NUMBER_OF_FRAMES")) is not None:
            return int(nb_frames)

    raise ValueError("Unable to find video frames number")


def _get_resolution(video_stream_info: Dict[str, Any]) -> tuple[int, int]:
    if (
        display_aspect_ratio := video_stream_info.get("display_aspect_ratio")
    ) is not None:
        return tuple(map(int, display_aspect_ratio.split(":")))

    raise ValueError("Unable to find video resolution")


def _get_fps(video_stream_info: Dict[str, Any]) -> float:
    if (avg_frame_rate := video_stream_info.get("avg_frame_rate")) is not None:
        x, y = map(int, avg_frame_rate.split("/", maxsplit=1))
        return x / y

    raise ValueError("Unable to find video resolution")


def get_video_meta(video_path: str) -> VideoMeta:
    info = probe(video_path)

    video_stream: Dict[str, Any] = info["streams"][0]
    return VideoMeta(
        duration=_get_duration(video_stream),
        frames_number=_get_frames_number(video_stream),
        resolution=_get_resolution(video_stream),
        fps=_get_fps(video_stream),
    )
