
import cv2
import mediapipe as mp
import time
from pathlib import Path

# Find the project root automatically.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "models" / "pose_landmarker_lite.task"

# Connections between MediaPipe's 33 body landmarks.
POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10),
    (11, 12),
    (11, 13), (13, 15),
    (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16),
    (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (27, 29), (29, 31), (27, 31),
    (24, 26), (26, 28), (28, 30), (30, 32), (28, 32),
]


def draw_pose(frame, landmarks):
    height, width = frame.shape[:2]
    points = []

    # Convert normalized landmark coordinates into pixel coordinates.
    for landmark in landmarks:
        x = int(landmark.x * width)
        y = int(landmark.y * height)

        if landmark.visibility >= 0.5:
            points.append((x, y))
        else:
            points.append(None)

    # Draw connecting lines first.
    for start, end in POSE_CONNECTIONS:
        if points[start] is not None and points[end] is not None:
            cv2.line(
                frame,
                points[start],
                points[end],
                (0, 255, 0),
                3,
            )

    # Draw visible landmarks.
    for point in points:
        if point is not None:
            cv2.circle(frame, point, 5, (0, 165, 255), -1)


def main():
    if not MODEL_PATH.exists():
        print("ERROR: Pose model not found!")
        print(f"Expected location: {MODEL_PATH}")
        return

    print("Loading MediaPipe Pose Landmarker...")

    options = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(MODEL_PATH)
        ),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Could not open webcam.")
        return

    previous_timestamp_ms = -1
    start_time = time.perf_counter()

    try:
        with mp.tasks.vision.PoseLandmarker.create_from_options(
            options
        ) as landmarker:

            print("Pose tracking started. Press Q to quit.")

            while True:
                success, frame = camera.read()

                if not success:
                    print("Could not read a webcam frame.")
                    break

                # Mirror the webcam view.
                frame = cv2.flip(frame, 1)

                rgb_frame = cv2.cvtColor(
                    frame, cv2.COLOR_BGR2RGB
                )

                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb_frame,
                )

                timestamp_ms = int(
                    (time.perf_counter() - start_time) * 1000
                )
                timestamp_ms = max(
                    timestamp_ms, previous_timestamp_ms + 1
                )
                previous_timestamp_ms = timestamp_ms

                result = landmarker.detect_for_video(
                    mp_image, timestamp_ms
                )

                if result.pose_landmarks:
                    landmarks = result.pose_landmarks[0]

                    draw_pose(frame, landmarks)

                    cv2.putText(
                        frame,
                        f"Body landmarks: {len(landmarks)}",
                        (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )

                    cv2.putText(
                        frame,
                        "Pose detected",
                        (15, 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )
                else:
                    cv2.putText(
                        frame,
                        "No body detected - move back into view",
                        (15, 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 255),
                        2,
                    )

                cv2.imshow("Speaker Body Pose Tracking", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    finally:
        camera.release()
        cv2.destroyAllWindows()

    print("Pose tracking stopped.")


if __name__ == "__main__":
    main()
