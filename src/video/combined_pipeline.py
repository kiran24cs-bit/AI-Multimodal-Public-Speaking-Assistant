
import argparse
import csv
import cv2
import mediapipe as mp
import time

from datetime import datetime
from pathlib import Path


# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = PROJECT_ROOT / "models"
OUTPUT_DIR = PROJECT_ROOT / "output"/"video_out"

FACE_MODEL = MODEL_DIR / "face_landmarker.task"
POSE_MODEL = MODEL_DIR / "pose_landmarker_lite.task"
HAND_MODEL = MODEL_DIR / "hand_landmarker.task"


# MediaPipe body connections.
POSE_CONNECTIONS = [
    (11, 12),
    (11, 13), (13, 15),
    (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (27, 29), (29, 31), (27, 31),
    (24, 26), (26, 28), (28, 30), (30, 32), (28, 32),
    (15, 17), (15, 19), (15, 21),
    (16, 18), (16, 20), (16, 22),
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10),
]

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]


# --------------------------------------------------
# 2. MODEL VALIDATION
# --------------------------------------------------

def validate_models():
    missing = [
        str(path)
        for path in (FACE_MODEL, POSE_MODEL, HAND_MODEL)
        if not path.is_file()
    ]

    if missing:
        print("ERROR: The following model files are missing:")
        for path in missing:
            print(f"  - {path}")
        return False

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return True


# --------------------------------------------------
# 3. DRAWING FUNCTIONS
# --------------------------------------------------

def pixel_point(landmark, width, height):
    x = max(0, min(width - 1, int(landmark.x * width)))
    y = max(0, min(height - 1, int(landmark.y * height)))
    return x, y


def draw_face(frame, landmarks):
    height, width = frame.shape[:2]

    for landmark in landmarks:
        x, y = pixel_point(landmark, width, height)
        cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)


def draw_pose(frame, landmarks):
    height, width = frame.shape[:2]
    points = []

    for landmark in landmarks:
        if landmark.visibility >= 0.5:
            points.append(pixel_point(landmark, width, height))
        else:
            points.append(None)

    for start, end in POSE_CONNECTIONS:
        if points[start] is not None and points[end] is not None:
            cv2.line(
                frame,
                points[start],
                points[end],
                (255, 180, 0),
                2,
            )

    for point in points:
        if point is not None:
            cv2.circle(frame, point, 4, (0, 165, 255), -1)


def draw_hands(frame, all_hands):
    height, width = frame.shape[:2]

    for landmarks in all_hands:
        points = [
            pixel_point(landmark, width, height)
            for landmark in landmarks
        ]

        for start, end in HAND_CONNECTIONS:
            cv2.line(
                frame,
                points[start],
                points[end],
                (255, 0, 255),
                2,
            )

        for point in points:
            cv2.circle(frame, point, 4, (255, 255, 0), -1)


def put_status(frame, text, y, color=(255, 255, 255)):
    cv2.putText(
        frame,
        text,
        (15, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        color,
        2,
        cv2.LINE_AA,
    )


# --------------------------------------------------
# 4. MEASUREMENTS
# --------------------------------------------------

def calculate_pose_metrics(landmarks):
    """
    Calculate geometric measurements from visible body landmarks.

    Shoulder tilt is the normalized vertical difference between
    shoulders. Torso offset is the horizontal difference between
    shoulder and hip midpoints.

    These measurements alone do not determine posture quality.
    """

    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]

    shoulder_tilt = None
    torso_offset = None

    shoulders_visible = (
        left_shoulder.visibility >= 0.5
        and right_shoulder.visibility >= 0.5
    )

    if shoulders_visible:
        shoulder_tilt = abs(
            left_shoulder.y - right_shoulder.y
        )

    left_hip = landmarks[23]
    right_hip = landmarks[24]

    hips_visible = (
        left_hip.visibility >= 0.5
        and right_hip.visibility >= 0.5
    )

    if shoulders_visible and hips_visible:
        shoulder_mid_x = (
            left_shoulder.x + right_shoulder.x
        ) / 2

        hip_mid_x = (
            left_hip.x + right_hip.x
        ) / 2

        torso_offset = shoulder_mid_x - hip_mid_x

    return shoulder_tilt, torso_offset


def get_top_blendshape(face_blendshapes):
    if not face_blendshapes:
        return "", ""

    top = max(
        face_blendshapes,
        key=lambda item: item.score,
    )

    return top.category_name, round(top.score, 4)


# --------------------------------------------------
# 5. MAIN PIPELINE
# --------------------------------------------------

def main(video_path=None):
    if not validate_models():
        return

    is_recorded_video = video_path is not None

    print("Initializing face, pose, and hand models...")

    face_options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(FACE_MODEL)
        ),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=1,
        output_face_blendshapes=True,
    )

    pose_options = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(POSE_MODEL)
        ),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    hand_options = mp.tasks.vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(HAND_MODEL)
        ),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    source = str(video_path) if is_recorded_video else 0
    camera = cv2.VideoCapture(source)

    if not camera.isOpened():
        print(f"ERROR: Could not open video source: {source}")
        camera.release()
        return

    fps = camera.get(cv2.CAP_PROP_FPS)

    if fps <= 0 or not (fps < float("inf")):
        fps = 30.0

    if is_recorded_video:
        print(f"Input video: {video_path}")
        print(f"Video FPS: {fps:.2f}")
    else:
        print("Input source: webcam")

    session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = OUTPUT_DIR / (
        f"presentation_metrics_{session_time}.csv"
    )

    csv_fields = [
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

    start_time = time.perf_counter()
    previous_timestamp_ms = -1
    frame_number = 0

    try:
        with (
            mp.tasks.vision.FaceLandmarker.create_from_options(
                face_options
            ) as face_detector,
            mp.tasks.vision.PoseLandmarker.create_from_options(
                pose_options
            ) as pose_detector,
            mp.tasks.vision.HandLandmarker.create_from_options(
                hand_options
            ) as hand_detector,
            open(
                csv_path,
                "w",
                newline="",
                encoding="utf-8",
            ) as csv_file,
        ):
            writer = csv.DictWriter(
                csv_file,
                fieldnames=csv_fields,
            )
            writer.writeheader()

            print("\nIntegrated pipeline is running.")
            print("Press Q to stop and save the CSV.")
            print(f"Output file: {csv_path}")

            while True:
                success, frame = camera.read()

                if not success:
                    if is_recorded_video:
                        print("End of recorded video reached.")
                    else:
                        print("ERROR: Could not read webcam frame.")
                    break

                # Mirror only webcam footage.
                if not is_recorded_video:
                    frame = cv2.flip(frame, 1)

                rgb_frame = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGR2RGB,
                )

                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb_frame,
                )

                # Recorded-video timestamps follow the video FPS.
                # Webcam timestamps use elapsed wall-clock time.
                if is_recorded_video:
                    timestamp_seconds = frame_number / fps
                else:
                    timestamp_seconds = (
                        time.perf_counter() - start_time
                    )

                timestamp_ms = int(timestamp_seconds * 1000)
                timestamp_ms = max(
                    timestamp_ms,
                    previous_timestamp_ms + 1,
                )
                previous_timestamp_ms = timestamp_ms

                # Run all three models on the same frame.
                face_result = face_detector.detect_for_video(
                    mp_image,
                    timestamp_ms,
                )
                pose_result = pose_detector.detect_for_video(
                    mp_image,
                    timestamp_ms,
                )
                hand_result = hand_detector.detect_for_video(
                    mp_image,
                    timestamp_ms,
                )

                face_detected = bool(face_result.face_landmarks)
                pose_detected = bool(pose_result.pose_landmarks)
                hand_count = len(hand_result.hand_landmarks)

                top_blendshape = ""
                top_blendshape_score = ""
                shoulder_tilt = None
                torso_offset = None

                # Face landmarks and blendshape signal.
                if face_detected:
                    draw_face(
                        frame,
                        face_result.face_landmarks[0],
                    )

                    if face_result.face_blendshapes:
                        (
                            top_blendshape,
                            top_blendshape_score,
                        ) = get_top_blendshape(
                            face_result.face_blendshapes[0]
                        )

                # Pose landmarks and geometric measurements.
                if pose_detected:
                    body_landmarks = pose_result.pose_landmarks[0]
                    draw_pose(frame, body_landmarks)

                    shoulder_tilt, torso_offset = (
                        calculate_pose_metrics(body_landmarks)
                    )

                # Hand landmarks.
                draw_hands(frame, hand_result.hand_landmarks)

                # Display detection status.
                put_status(
                    frame,
                    f"Face: {'Detected' if face_detected else 'Not detected'}",
                    30,
                    (0, 255, 0) if face_detected else (0, 0, 255),
                )

                put_status(
                    frame,
                    f"Body: {'Detected' if pose_detected else 'Not detected'}",
                    60,
                    (0, 255, 0) if pose_detected else (0, 0, 255),
                )

                put_status(
                    frame,
                    f"Hands detected: {hand_count}",
                    90,
                    (255, 255, 0),
                )

                if top_blendshape:
                    put_status(
                        frame,
                        f"Top face signal: {top_blendshape} "
                        f"({top_blendshape_score})",
                        120,
                    )

                put_status(
                    frame,
                    f"Elapsed: {timestamp_seconds:.1f}s",
                    150,
                )

                # Extract wrist coordinates when visible.
                left_wrist_x = ""
                left_wrist_y = ""
                right_wrist_x = ""
                right_wrist_y = ""

                if pose_detected:
                    body_landmarks = pose_result.pose_landmarks[0]
                    left_wrist = body_landmarks[15]
                    right_wrist = body_landmarks[16]

                    if left_wrist.visibility >= 0.5:
                        left_wrist_x = round(left_wrist.x, 5)
                        left_wrist_y = round(left_wrist.y, 5)

                    if right_wrist.visibility >= 0.5:
                        right_wrist_x = round(right_wrist.x, 5)
                        right_wrist_y = round(right_wrist.y, 5)

                writer.writerow({
                    "timestamp_seconds": round(
                        timestamp_seconds, 3
                    ),
                    "face_detected": face_detected,
                    "top_blendshape": top_blendshape,
                    "top_blendshape_score": top_blendshape_score,
                    "pose_detected": pose_detected,
                    "shoulder_tilt_normalized": (
                        round(shoulder_tilt, 5)
                        if shoulder_tilt is not None
                        else ""
                    ),
                    "torso_offset_normalized": (
                        round(torso_offset, 5)
                        if torso_offset is not None
                        else ""
                    ),
                    "hand_count": hand_count,
                    "left_wrist_x": left_wrist_x,
                    "left_wrist_y": left_wrist_y,
                    "right_wrist_x": right_wrist_x,
                    "right_wrist_y": right_wrist_y,
                })

                # Periodically flush results to disk.
                if frame_number % 30 == 0:
                    csv_file.flush()

                frame_number += 1

                cv2.imshow(
                    "Integrated Presentation Analysis",
                    frame,
                )

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("Stopped by user.")
                    break

    except Exception as error:
        print(f"\nPipeline error: {error}")
        raise

    finally:
        camera.release()
        cv2.destroyAllWindows()

    print("\nAnalysis session ended.")
    print(f"Frames processed: {frame_number}")
    print(f"CSV saved to: {csv_path}")


# --------------------------------------------------
# 6. COMMAND-LINE ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Integrated face, pose, and hand presentation analysis."
        )
    )

    parser.add_argument(
        "video",
        nargs="?",
        help=(
            "Path to a prerecorded video. "
            "Omit this argument to use the webcam."
        ),
    )

    args = parser.parse_args()

    if args.video:
        video_path = Path(args.video).expanduser()

        if not video_path.is_file():
            parser.error(f"Video file not found: {video_path}")

        main(video_path)
    else:
        main()
