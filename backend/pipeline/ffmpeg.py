"""
Scene-cut detection via ffmpeg.

TODO (video pipeline person): replace the stub below with real ffmpeg scene detection.

Real implementation outline:
    1. Download the video file alongside the audio in extract_video() (yt-dlp -f "bestvideo[ext=mp4]")
    2. Run ffmpeg scene filter:
           ffmpeg -i <video_path> -vf "select='gt(scene,0.3)',showinfo" -f null - 2>&1
    3. Count "Parsed_showinfo" lines → total scene cuts
    4. Return round(total_cuts / (duration_sec / 60))
"""


def detect_scene_cuts(video_path: str | None, duration_sec: int) -> int:
    """
    Returns cuts per minute from ffmpeg scene detection.

    Stubbed — returns 0 until real video download + ffmpeg is wired up.
    pipeline/video.py falls back to audio-onset detection when this returns 0.
    """
    return 0
