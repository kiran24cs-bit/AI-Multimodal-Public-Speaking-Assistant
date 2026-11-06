
import csv
import json
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output" / "video_out"

CSV_FIELDS = [
    "timestamp_seconds",
    "face_detected",
    "top_blendshape",
    "top_blendshape_score",
    "pose_detected",
    "shoulder_tilt_normalized",
    "torso_offset_normalized",
    "hand_count",
    "left_wrist_x",
    "left_wrist_y",
    "right_wrist_x",
    "right_wrist_y",
]


def safe_round(value, digits=5):
    if value is None:
        return ""

    try:
        number = float(value)
        if not math.isfinite(number):
            return ""
        return round(number, digits)
    except (TypeError, ValueError):
        return ""


def visible_wrist(landmarks, index):
    if len(landmarks) <= index:
        return "", ""

    wrist = landmarks[index]

    visibility = wrist.get("visibility")
    if visibility is None or visibility < 0.5:
        return "", ""

    return (
        safe_round(wrist.get("x")),
        safe_round(wrist.get("y")),
    )


def export_metrics(json_path):
    with json_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    session_id = data.get("session_id", "")
    if not session_id.startswith("presentation_"):
        raise ValueError(
            f"Unexpected session ID in {json_path.name}: {session_id}"
        )

    timestamp_suffix = session_id[len("presentation_"):]
    csv_path = OUTPUT_DIR / (
        f"presentation_metrics_{timestamp_suffix}.csv"
    )

    rows = []


    for frame in data.get("frames", []):
        quality = frame.get("quality") or {}

        # Preserve compatibility with older JSON files that lack this flag.
        analysis_performed = quality.get("analysis_performed", True)

        # Keep unsampled frames in the CSV, but don't treat them as
        # frames where detection was attempted and failed.
        if not analysis_performed:
            row = {field: "" for field in CSV_FIELDS}
            row["timestamp_seconds"] = safe_round(
                frame.get("timestamp_seconds"), 3
            )
            rows.append(row)
            continue

        face = frame.get("face") or {}
        body = frame.get("body") or {}
        hands = frame.get("hands") or {}


        blendshapes = face.get("blendshapes") or {}

        if blendshapes:
            top_name = max(blendshapes, key=blendshapes.get)
            top_score = safe_round(blendshapes[top_name], 4)
        else:
            top_name = ""
            top_score = ""

        measurements = body.get("measurements") or {}
        body_landmarks = body.get("landmarks") or []

        left_wrist_x, left_wrist_y = visible_wrist(
            body_landmarks, 15
        )
        right_wrist_x, right_wrist_y = visible_wrist(
            body_landmarks, 16
        )

        rows.append({
            "timestamp_seconds": safe_round(
                frame.get("timestamp_seconds"), 3
            ),
            "face_detected": bool(face.get("detected", False)),
            "top_blendshape": top_name,
            "top_blendshape_score": top_score,
            "pose_detected": bool(body.get("detected", False)),
            "shoulder_tilt_normalized": safe_round(
                measurements.get("shoulder_tilt_normalized")
            ),
            "torso_offset_normalized": safe_round(
                measurements.get("torso_offset_normalized")
            ),
            "hand_count": hands.get("detected_count", 0),
            "left_wrist_x": left_wrist_x,
            "left_wrist_y": left_wrist_y,
            "right_wrist_x": right_wrist_x,
            "right_wrist_y": right_wrist_y,
        })

    with csv_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print("\nCSV EXPORT COMPLETED")
    print(f"Source JSON: {json_path.name}")
    print(f"Rows exported: {len(rows)}")
    print(f"CSV saved to: {csv_path}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_files = list(
        OUTPUT_DIR.glob("presentation_*_visual_analysis.json")
    )

    if not json_files:
        raise FileNotFoundError(
            "No visual analysis JSON found in output/video_out. "
            "Run analyze_video_json.py first."
        )

    latest_json = max(
        json_files, key=lambda path: path.stat().st_mtime
    )

    export_metrics(latest_json)


if __name__ == "__main__":
    main()
