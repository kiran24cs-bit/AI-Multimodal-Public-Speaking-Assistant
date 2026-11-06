
import cv2
import mediapipe as mp
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "models" / "hand_landmarker.task"

# Connections between the 21 landmarks of each hand.
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]


def draw_hand(frame, landmarks):
    height, width = frame.shape[:2]
    points = []

    for landmark in landmarks:
        x = int(landmark.x * width)
        y = int(landmark.y * height)
        points.append((x, y))

    # Draw the finger and palm connections.
    for start, end in HAND_CONNECTIONS:
        cv2.line(
            frame,
            points[start],
            points[end],
            (0, 255, 0),
            2,
        )

    # Draw the 21 landmarks.
    for point in points:
        cv2.circle(frame, point, 4, (0, 165, 255), -1)


def main():
    if not MODEL_PATH.exists():
        print("ERROR: Hand model not found!")
        print(f"Expected location: {MODEL_PATH}")
        return

    options = mp.tasks.vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(MODEL_PATH)
        ),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("ERROR: Could not open webcam.")
        return

    previous_timestamp_ms = -1
    start_time = time.perf_counter()

    try:
        with mp.tasks.vision.HandLandmarker.create_from_options(
            options
        ) as landmarker:

            print("Hand tracking started. Press Q to quit.")

            while True:
                success, frame = camera.read()

                if not success:
                    print("Could not read webcam frame.")
                    break

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

                hand_count = len(result.hand_landmarks)

                for hand_landmarks in result.hand_landmarks:
                    draw_hand(frame, hand_landmarks)

                cv2.putText(
                    frame,
                    f"Hands detected: {hand_count}",
                    (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )

                cv2.putText(
                    frame,
                    "Show your hands to the camera",
                    (15, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )

                cv2.imshow("Speaker Hand Gesture Tracking", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    finally:
        camera.release()
        cv2.destroyAllWindows()

    print("Hand tracking stopped.")


if __name__ == "__main__":
    main()
