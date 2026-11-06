
import csv
import json
import glob
import os
from pathlib import Path


# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

BLINK_THRESHOLD = 0.50
MIN_BLINK_DURATION = 0.03
MAX_BLINK_DURATION = 0.60

# The video analyzer samples at approximately 15 FPS.
ANALYSIS_FPS = 15.0
SAMPLE_INTERVAL = 1.0 / ANALYSIS_FPS

# Merge high-score runs separated by short gaps.
MERGE_GAP = 0.10

ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = ROOT / "output" / "video_out"
REPORT_DIR = OUTPUT_DIR / "facial_signal_reports"
CSV_PATH = REPORT_DIR / "candidate_blinks.csv"


# --------------------------------------------------
# 2. FIND LATEST VISUAL-ANALYSIS JSON
# --------------------------------------------------

def find_latest_json():
    files = list(OUTPUT_DIR.glob("*visual_analysis.json"))

    if not files:
        raise FileNotFoundError(
            f"No visual-analysis JSON found in: {OUTPUT_DIR}"
        )

    return max(files, key=lambda path: path.stat().st_mtime)


# --------------------------------------------------
# 3. LOAD AND VALIDATE JSON
# --------------------------------------------------

def load_frames(json_path):
    with json_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    frames = data.get("frames", [])

    if not isinstance(frames, list):
        raise ValueError(
            "Invalid visual-analysis JSON: 'frames' must be a list."
        )

    return frames


# --------------------------------------------------
# 4. EXTRACT BLINK SCORES
# --------------------------------------------------

def extract_samples(frames):
    samples = []

    for frame in frames:
        if not isinstance(frame, dict):
            continue

        # Skip frames intentionally omitted from detailed analysis.
        quality = frame.get("quality", {})

        if quality.get("analysis_performed") is False:
            continue

        timestamp = frame.get("timestamp_seconds")

        if not isinstance(timestamp, (int, float)):
            continue

        face = frame.get("face", {})

        if not isinstance(face, dict):
            continue

        if not face.get("detected", False):
            # Do not infer a blink when no face is detected.
            continue

        shapes = face.get("blendshapes", {})

        if not isinstance(shapes, dict):
            continue

        left = shapes.get("eyeBlinkLeft")
        right = shapes.get("eyeBlinkRight")

        if not isinstance(left, (int, float)):
            continue

        if not isinstance(right, (int, float)):
            continue

        score = max(float(left), float(right))

        samples.append({
            "timestamp": float(timestamp),
            "score": score,
        })

    samples.sort(key=lambda sample: sample["timestamp"])

    return samples


# --------------------------------------------------
# 5. GROUP HIGH-SCORE SAMPLES
# --------------------------------------------------

def find_candidate_runs(samples):
    runs = []
    current_run = []

    for sample in samples:
        if sample["score"] < BLINK_THRESHOLD:
            if current_run:
                runs.append(current_run)
                current_run = []

            continue

        if not current_run:
            current_run = [sample]
            continue

        previous_time = current_run[-1]["timestamp"]
        time_gap = sample["timestamp"] - previous_time

        # Join nearby high-score samples, including across brief
        # unsampled intervals, but do not merge distant events.
        if time_gap <= SAMPLE_INTERVAL + MERGE_GAP:
            current_run.append(sample)
        else:
            runs.append(current_run)
            current_run = [sample]

    if current_run:
        runs.append(current_run)

    return runs


# --------------------------------------------------
# 6. CONVERT RUNS TO CANDIDATE EVENTS
# --------------------------------------------------

def build_events(runs):
    events = []

    for run in runs:
        start_time = run[0]["timestamp"]
        end_time = run[-1]["timestamp"]

        # A single high-score sample still represents an interval
        # of approximately one analysis sampling period.
        duration = end_time - start_time + SAMPLE_INTERVAL

        peak_score = max(sample["score"] for sample in run)

        # Reject events outside the configured duration limits.
        if not (
            MIN_BLINK_DURATION
            <= duration
            <= MAX_BLINK_DURATION
        ):
            continue

        events.append({
            "start_seconds": round(start_time, 3),
            "end_seconds": round(end_time, 3),
            "duration_seconds": round(duration, 3),
            "peak_score": round(peak_score, 3),
            "status": "candidate",
            "note": (
                "Estimated from sampled eye-blink scores; "
                "verify against original video"
            ),
        })

    return events


# --------------------------------------------------
# 7. SAVE CANDIDATE CSV
# --------------------------------------------------

def save_events(events):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    columns = [
        "start_seconds",
        "end_seconds",
        "duration_seconds",
        "peak_score",
        "status",
        "note",
    ]

    with CSV_PATH.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(events)


# --------------------------------------------------
# 8. MAIN
# --------------------------------------------------

def main():
    json_path = find_latest_json()
    frames = load_frames(json_path)

    samples = extract_samples(frames)
    runs = find_candidate_runs(samples)
    events = build_events(runs)

    save_events(events)

    print("=" * 60)
    print("BLINK CANDIDATE DETECTION")
    print("=" * 60)
    print(f"Source JSON: {json_path}")
    print(f"Total source frames: {len(frames)}")
    print(f"Frames with usable blink scores: {len(samples)}")
    print(f"High-score runs: {len(runs)}")
    print(f"Candidate blink events: {len(events)}")
    print(f"Candidate CSV: {CSV_PATH}")
    print()
    print(
        "IMPORTANT: These are unvalidated candidates, "
        "not confirmed blink counts."
    )
    print("Review candidates against the original video.")
    print("Original visual-analysis JSON was not modified.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(f"Blink detection failed: {error}")
