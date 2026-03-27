import subprocess, tempfile, os, json
import numpy as np
import librosa
from pipeline.ffmpeg import detect_scene_cuts


def extract_video(url: str, out_dir: str) -> dict:
    """Download audio + extract transcript via yt-dlp. Returns paths + metadata."""
    meta_path = os.path.join(out_dir, "meta.json")
    audio_path = os.path.join(out_dir, "audio.wav")

    # Metadata
    subprocess.run([
        "yt-dlp", "--skip-download", "--print-json", "-o", meta_path, url
    ], capture_output=True, check=False)

    # Audio (wav for librosa)
    subprocess.run([
        "yt-dlp", "-x", "--audio-format", "wav",
        "-o", audio_path, url
    ], capture_output=True, check=False)

    # Transcript (auto-subs)
    subprocess.run([
        "yt-dlp", "--write-auto-sub", "--sub-format", "json3",
        "--skip-download", "-o", os.path.join(out_dir, "sub"), url
    ], capture_output=True, check=False)

    # Parse metadata
    meta = {}
    for f in os.listdir(out_dir):
        if f.endswith(".json") and f != "meta.json":
            with open(os.path.join(out_dir, f)) as fh:
                meta = json.load(fh)
            break
    if not meta:
        # fallback: yt-dlp --dump-json
        result = subprocess.run(["yt-dlp", "--dump-json", url], capture_output=True, text=True)
        if result.returncode == 0:
            meta = json.loads(result.stdout)

    # Transcript text
    transcript = ""
    for f in os.listdir(out_dir):
        if f.endswith(".json3") or (f.startswith("sub") and f.endswith(".json")):
            with open(os.path.join(out_dir, f)) as fh:
                sub_data = json.load(fh)
            events = sub_data.get("events", [])
            transcript = " ".join(
                seg.get("utf8", "") for e in events for seg in e.get("segs", [])
            ).strip()
            break

    return {
        "title": meta.get("title", ""),
        "description": meta.get("description", ""),
        "duration": meta.get("duration", 0),
        "channel": meta.get("channel", meta.get("uploader", "")),
        "thumbnail": meta.get("thumbnail", ""),
        "audio_path": audio_path if os.path.exists(audio_path) else None,
        "transcript": transcript,
    }


def analyze_audio(audio_path: str) -> dict:
    """Compute cuts-per-minute proxy, volume spikes, and spectral chaos from audio."""
    if not audio_path or not os.path.exists(audio_path):
        return {"cuts_per_min": 0, "avg_volume_variance": 0.0, "volume_spike_frequency": 0}

    y, sr = librosa.load(audio_path, sr=22050, mono=True, duration=300)  # cap at 5 min

    # Onset strength as proxy for cuts/hard edits
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, units="time")
    duration_min = len(y) / sr / 60
    cuts_per_minute = len(onsets) / max(duration_min, 0.1)

    # Volume spikes: frames where RMS > 2.5x median
    rms = librosa.feature.rms(y=y)[0]
    median_rms = np.median(rms)
    spike_binary = (rms > 2.5 * median_rms).astype(int)
    # avg_volume_variance: fraction of frames at high volume (0.0–1.0)
    avg_volume_variance = round(float(np.sum(spike_binary) / max(len(rms), 1)), 4)
    # volume_spike_frequency: spike onset events per minute
    spike_events = int(np.sum(np.diff(spike_binary) == 1))
    volume_spike_frequency = int(round(spike_events / max(duration_min, 0.1)))

    return {
        "cuts_per_min": int(round(cuts_per_minute)),
        "avg_volume_variance": avg_volume_variance,
        "volume_spike_frequency": volume_spike_frequency,
    }


def run_pipeline(url: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        video_data = extract_video(url, tmp)
        audio_metrics = analyze_audio(video_data["audio_path"])
        duration_sec = int(video_data.get("duration", 0))
        # Use ffmpeg scene detection when available; fall back to audio-onset proxy
        scene_cuts = detect_scene_cuts(
            video_path=video_data.get("video_path"),  # None until video download is added
            duration_sec=duration_sec,
        )
        if scene_cuts > 0:
            audio_metrics["cuts_per_min"] = scene_cuts

    result = {**video_data, **audio_metrics, "audio_path": None}
    result["duration_sec"] = duration_sec
    result.pop("duration", None)
    return result
