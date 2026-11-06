import argparse
import csv
from pathlib import Path

import cv2
import numpy as np


# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

REPORT_DIR = ROOT / "output" / "video_out" / "facial_signal_reports"
CSV_PATH = REPORT_DIR / "candidate_blinks.csv"
OUTPUT_PATH = REPORT_DIR / "blink_review_contact_sheet.jpg"


# --------------------------------------------------
# 2. FIND VIDEO
# --------------------------------------------------

def find_video(video_argument=None):
    if video_argument:
        video_path = Path(video_argument).expanduser().resolve()

        if not video_path.is_file():
            raise FileNotFoundError(
                f"Video file not found: {video_path}"
            )

        return video_path

    videos = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.suffix.lower() == ".mp4"
        and ".venv" not in path.parts
        and "node_modules" not in path.parts
        and "output" not in path.parts
    ]

    if not videos:
        raise FileNotFoundError(
            "No MP4 video found. Supply its path as an argument."
        )

    return next(
        (
            path for path in videos
            if path.name.lower() == "testing video.mp4"
        ),
        videos[0],
    )


# --------------------------------------------------
# 3. LOAD BLINK CANDIDATES
# --------------------------------------------------


def load_events():
    if not CSV_PATH.is_file():
        raise FileNotFoundError(
            f"Candidate CSV not found: {CSV_PATH}\n"
            "Run src\\video\\detect_blinks.py first."
        )

    with CSV_PATH.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        events = list(csv.DictReader(file))

    if not events:
        return []

    required = {"start_seconds", "end_seconds"}

    if not required.issubset(events[0].keys()):
        raise ValueError(
            "Candidate CSV must contain start_seconds and end_seconds."
        )

    return events



# --------------------------------------------------
# 4. CREATE CONTACT SHEET
# --------------------------------------------------

def create_contact_sheet(video_path, events):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if fps <= 0 or frame_count <= 0:
            raise ValueError(
                "Could not determine the video's frame rate or duration."
            )

        duration = frame_count / fps

        thumb_width = 320
        thumb_height = 180
        label_height = 28
        gap = 8
        columns = 3
        rows = len(events)

        sheet_width = (
            columns * thumb_width + (columns + 1) * gap
        )
        sheet_height = (
            rows * (thumb_height + label_height)
            + (rows + 1) * gap
        )

        sheet = np.full(
            (sheet_height, sheet_width, 3),
            255,
            dtype=np.uint8,
        )

        def get_frame(seconds):
            seconds = max(
                0,
                min(seconds, max(0, duration - 0.01)),
            )

            cap.set(
                cv2.CAP_PROP_POS_MSEC,
                seconds * 1000,
            )

            success, frame = cap.read()

            if not success:
                return None

            return cv2.resize(
                frame,
                (thumb_width, thumb_height),
            )

        for row, event in enumerate(events):
            start = float(event["start_seconds"])
            end = float(event["end_seconds"])

            if start < 0 or end < start:
                print(
                    f"Skipping invalid candidate {row + 1}."
                )
                continue

            midpoint = (start + end) / 2

            samples = [
                (max(0, start - 0.10), "BEFORE"),
                (midpoint, "EVENT"),
                (min(duration - 0.01, end + 0.10), "AFTER"),
            ]

            y = gap + row * (
                thumb_height + label_height + gap
            )

            event_label = (
                f"Candidate {row + 1}: "
                f"{start:.3f}-{end:.3f}s "
                f"(duration {end - start:.3f}s)"
            )

            cv2.putText(
                sheet,
                event_label,
                (gap, y + 14),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (40, 40, 40),
                1,
                cv2.LINE_AA,
            )

            for col, (timestamp, label) in enumerate(samples):
                x = gap + col * (thumb_width + gap)
                frame_y = y + label_height

                frame = get_frame(timestamp)

                if frame is not None:
                    sheet[
                        frame_y:frame_y + thumb_height,
                        x:x + thumb_width,
                    ] = frame

                cv2.putText(
                    sheet,
                    f"{label} | {timestamp:.3f}s",
                    (x + 5, frame_y + thumb_height - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (20, 20, 20),
                    1,
                    cv2.LINE_AA,
                )

        success = cv2.imwrite(
            str(OUTPUT_PATH),
            sheet,
        )

        if not success:
            raise OSError(
                f"Could not save contact sheet: {OUTPUT_PATH}"
            )

    finally:
        cap.release()

    print(f"Video: {video_path}")
    print(f"Candidates reviewed: {len(events)}")
    print(f"Contact sheet: {OUTPUT_PATH}")
    print(
        "Open the image and compare each "
        "BEFORE / EVENT / AFTER sequence."
    )


# --------------------------------------------------
# 5. MAIN
# --------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Create a visual review sheet for candidate blinks."
    )

    parser.add_argument(
        "video",
        nargs="?",
        help="Optional path to the recorded MP4 video.",
    )

    args = parser.parse_args()

    try:
        events = load_events()

        if not events:
            print("Candidate blink events: 0")
            print("No contact sheet was generated.")
            print(
                "This step is being skipped because there are "
                "no candidate events to review."
            )
            return

        video_path = find_video(args.video)
        create_contact_sheet(video_path, events)

    except (FileNotFoundError, ValueError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
