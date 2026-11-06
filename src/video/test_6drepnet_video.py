
import argparse
import csv
import time
from pathlib import Path

import cv2
from sixdrepnet import SixDRepNet


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output" / "video_out" / "head_pose_reports"

SAMPLE_FPS = 2
MIN_FACE_SIZE = (60, 60)


def main():
    parser = argparse.ArgumentParser(
        description="Estimate head pose from a prerecorded video."
    )
    parser.add_argument(
        "video",
        help="Path to the prerecorded video file",
    )
    args = parser.parse_args()

    video_path = Path(args.video).expanduser()

    if not video_path.is_file():
        raise FileNotFoundError(f"Video not found: {video_path}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / f"{video_path.stem}_head_pose_samples.csv"

    cascade_path = (
        cv2.data.haarcascades
        + "haarcascade_frontalface_default.xml"
    )
    face_detector = cv2.CascadeClassifier(cascade_path)

    if face_detector.empty():
        raise RuntimeError("Could not load OpenCV face detector.")

    print("Loading 6DRepNet model...")
    model = SixDRepNet(gpu_id=-1)
    print("Model loaded.")

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / video_fps if video_fps > 0 else 0

    if video_fps <= 0:
        cap.release()
        raise RuntimeError("Could not determine the video's frame rate.")

    frame_step = max(1, round(video_fps / SAMPLE_FPS))

    print(f"Input video: {video_path}")
    print(f"Video FPS: {video_fps:.3f}")
    print(f"Video duration: {duration:.2f} seconds")
    print(f"Approximate sampling interval: {frame_step / video_fps:.3f}s")
    print(f"Output CSV: {csv_path}")
    print()

    columns = [
        "timestamp_seconds",
        "frame_number",
        "face_detected",
        "pitch_degrees",
        "yaw_degrees",
        "roll_degrees",
        "inference_seconds",
        "status",
    ]

    rows_written = 0
    faces_found = 0
    start_time = time.perf_counter()
    frame_number = 0

    try:
        with csv_path.open(
            "w", newline="", encoding="utf-8"
        ) as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=columns)
            writer.writeheader()

            while True:
                success, frame = cap.read()

                if not success:
                    break

                if frame_number % frame_step == 0:
                    timestamp = frame_number / video_fps

                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_detector.detectMultiScale(
                        gray,
                        scaleFactor=1.1,
                        minNeighbors=5,
                        minSize=MIN_FACE_SIZE,
                    )

                    row = {
                        "timestamp_seconds": round(timestamp, 3),
                        "frame_number": frame_number,
                        "face_detected": False,
                        "pitch_degrees": "",
                        "yaw_degrees": "",
                        "roll_degrees": "",
                        "inference_seconds": "",
                        "status": "no_face_detected",
                    }

                    if len(faces) > 0:
                        x, y, width, height = max(
                            faces,
                            key=lambda box: box[2] * box[3],
                        )

                        pad_x = int(width * 0.15)
                        pad_y = int(height * 0.15)

                        x1 = max(0, x - pad_x)
                        y1 = max(0, y - pad_y)
                        x2 = min(frame.shape[1], x + width + pad_x)
                        y2 = min(frame.shape[0], y + height + pad_y)

                        face_crop = frame[y1:y2, x1:x2]

                        row["face_detected"] = True
                        faces_found += 1

                        try:
                            inference_start = time.perf_counter()
                            pitch, yaw, roll = model.predict(face_crop)
                            inference_time = (
                                time.perf_counter() - inference_start
                            )

                            row["pitch_degrees"] = round(
                                float(pitch[0]), 3
                            )
                            row["yaw_degrees"] = round(
                                float(yaw[0]), 3
                            )
                            row["roll_degrees"] = round(
                                float(roll[0]), 3
                            )
                            row["inference_seconds"] = round(
                                inference_time, 4
                            )
                            row["status"] = "ok"

                        except Exception as exc:
                            row["status"] = (
                                f"prediction_error: {type(exc).__name__}"
                            )

                    writer.writerow(row)
                    rows_written += 1

                    if rows_written % 20 == 0:
                        print(
                            f"Processed {rows_written} samples; "
                            f"faces detected: {faces_found}"
                        )

                frame_number += 1

    finally:
        cap.release()

    elapsed = time.perf_counter() - start_time

    print("\nHEAD-POSE ANALYSIS COMPLETE")
    print("---------------------------")
    print(f"Samples written: {rows_written}")
    print(f"Samples with a detected face: {faces_found}")
    print(f"Elapsed time: {elapsed:.2f} seconds")
    print(f"CSV saved to: {csv_path}")


if __name__ == "__main__":
    main()
