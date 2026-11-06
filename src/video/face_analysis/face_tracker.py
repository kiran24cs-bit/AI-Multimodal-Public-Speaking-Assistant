
import cv2
import mediapipe as mp
from pathlib import Path


# Locate the downloaded model inside the project.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "models" / "face_landmarker.task"


def main():
    if not MODEL_PATH.exists():
        print(f"Face model not found: {MODEL_PATH}")
        return

    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(MODEL_PATH)
        ),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=1,
        output_face_blendshapes=True,
    )

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Could not access webcam.")
        return

    previous_time_ms = -1

    try:
        with mp.tasks.vision.FaceLandmarker.create_from_options(
            options
        ) as landmarker:
            print("Face tracking started. Press Q to quit.")

            while True:
                success, frame = camera.read()

                if not success:
                    print("Could not read webcam frame.")
                    break

                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb,
                )

                # VIDEO mode requires increasing timestamps.
                timestamp_ms = max(
                    int(cv2.getTickCount() * 1000 / cv2.getTickFrequency()),
                    previous_time_ms + 1,
                )
                previous_time_ms = timestamp_ms

                result = landmarker.detect_for_video(
                    mp_image, timestamp_ms
                )

                if result.face_landmarks:
                    face = result.face_landmarks[0]
                    height, width = frame.shape[:2]

                    # Draw detected facial landmarks.
                    for point in face:
                        x = int(point.x * width)
                        y = int(point.y * height)

                        if 0 <= x < width and 0 <= y < height:
                            cv2.circle(
                                frame, (x, y), 1, (0, 255, 0), -1
                            )

                    cv2.putText(
                        frame,
                        f"Landmarks detected: {len(face)}",
                        (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        (0, 255, 0),
                        2,
                    )

                    # Display the three highest blendshape scores.
                    if result.face_blendshapes:
                        categories = result.face_blendshapes[0]
                        top_scores = sorted(
                            categories,
                            key=lambda item: item.score,
                            reverse=True,
                        )[:3]

                        for i, item in enumerate(top_scores):
                            text = (
                                f"{item.category_name}: "
                                f"{item.score:.2f}"
                            )
                            cv2.putText(
                                frame,
                                text,
                                (15, 60 + i * 28),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.55,
                                (255, 200, 0),
                                2,
                            )
                else:
                    cv2.putText(
                        frame,
                        "No face detected",
                        (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2,
                    )

                cv2.imshow("Speaker Face Analysis", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    except Exception as error:
        print(f"Face tracking error: {error}")

    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
