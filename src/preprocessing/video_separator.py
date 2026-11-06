
import cv2
import json
import shutil
import subprocess
from pathlib import Path

# Project root: presentation-ai/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 1. Define the raw folder
RAW_DIR = Path("data") / "raw"

# 2. Search for any .mp4 files in the folder
available_videos = list(RAW_DIR.glob("*.mp4"))

if not available_videos:
    raise FileNotFoundError(f"No .mp4 files found in {RAW_DIR.resolve()}. Please drop a video in the folder.")

# 3. Automatically grab the first video it finds!
VIDEO_PATH = available_videos[0]

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_VIDEO_PATH = OUTPUT_DIR / "presentation.mp4"

AUDIO_PATH = OUTPUT_DIR / "presentation.wav"
METADATA_PATH = OUTPUT_DIR / "video_metadata.json"


def extract_video_metadata(video_path):
    """Read video properties using OpenCV."""

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open video: {video_path}"
        )

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(
        cap.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    width = int(
        cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    )
    height = int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    duration = (
        frame_count / fps
        if fps and fps > 0
        else None
    )

    metadata = {
        "video_filename": video_path.name,
        "fps": fps,
        "frame_count": frame_count,
        "width": width,
        "height": height,
        "duration_seconds": duration
    }

    cap.release()
    return metadata


def extract_audio(video_path, audio_path, duration=None):
    """Extract mono, 16 kHz WAV audio using FFmpeg. If no audio stream is present, generate silent audio."""

    command = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(audio_path)
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        err_text = result.stderr or ""
        if "does not contain any stream" in err_text or "Output file does not contain any stream" in err_text:
            print("Warning: Video has no audio stream. Generating silent audio fallback...")
            dur = duration if (duration and duration > 0) else 10.0
            fallback_cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", "anullsrc=r=16000:cl=mono",
                "-t", str(dur),
                "-c:a", "pcm_s16le",
                str(audio_path)
            ]
            fallback_res = subprocess.run(fallback_cmd, capture_output=True, text=True)
            if fallback_res.returncode != 0:
                raise RuntimeError(f"Failed to generate fallback audio: {fallback_res.stderr[-500:]}")
            print(f"Silent fallback audio saved to: {audio_path}")
            return

        raise RuntimeError(
            "FFmpeg audio extraction failed:\n"
            + result.stderr[-2000:]
        )

    if not audio_path.exists():
        raise RuntimeError("Audio file was not created.")

    print(f"Audio saved to: {audio_path}")


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if not VIDEO_PATH.exists():
        raise FileNotFoundError(
            f"Video not found: {VIDEO_PATH}\n"
            "Place your video at data/raw/presentation.mp4"
        )

    print("Reading video metadata...")

    metadata = extract_video_metadata(VIDEO_PATH)

    with open(
        METADATA_PATH,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(metadata, file, indent=4)

    print(json.dumps(metadata, indent=4))

    print("\nExtracting audio...")

    extract_audio(
        VIDEO_PATH,
        AUDIO_PATH,
        duration=metadata.get("duration_seconds")
    )

    shutil.copy2(VIDEO_PATH, OUTPUT_VIDEO_PATH)

    print("\nSTEP 1 COMPLETED SUCCESSFULLY")
    print(f"Metadata: {METADATA_PATH}")
    print(f"Audio: {AUDIO_PATH}")



if __name__ == "__main__":
    main()

