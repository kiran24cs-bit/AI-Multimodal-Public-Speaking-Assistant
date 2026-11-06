
import json
import glob
import os
import statistics

# Find the most recently generated visual-analysis JSON.
files = glob.glob("output/video_out/*visual_analysis.json")

if not files:
    raise FileNotFoundError(
        "No visual-analysis JSON found in the output folder."
    )

json_path = max(files, key=os.path.getmtime)

with open(json_path, "r", encoding="utf-8") as file:
    data = json.load(file)

frames = data.get("frames", [])

detected_frames = [
    frame for frame in frames
    if frame.get("face", {}).get("detected", False)
]

print("=" * 55)
print("FACIAL SIGNAL TEST")
print("=" * 55)
print("Input file:", json_path)
print("Total frames:", len(frames))
print("Frames with a detected face:", len(detected_frames))

if not detected_frames:
    print("No detected face frames available.")
    raise SystemExit(1)

# Inspect which blendshape signals are present.
first_shapes = detected_frames[0]["face"].get(
    "blendshapes", {}
)

print("\nAvailable blendshape names:")
print(", ".join(first_shapes.keys()) or "No blendshapes found")

# Check the signals relevant to eye blinks and mouth movement.
target_signals = [
    "eyeBlinkLeft",
    "eyeBlinkRight",
    "jawOpen",
    "mouthClose",
    "mouthSmileLeft",
    "mouthSmileRight",
]

print("\nSignal statistics:")

for signal in target_signals:
    values = []

    for frame in detected_frames:
        shapes = frame.get("face", {}).get(
            "blendshapes", {}
        )

        value = shapes.get(signal)

        if isinstance(value, (int, float)):
            values.append(float(value))

    if values:
        print(
            f"{signal}: "
            f"min={min(values):.3f}, "
            f"max={max(values):.3f}, "
            f"mean={statistics.mean(values):.3f}, "
            f"samples={len(values)}"
        )
    else:
        print(f"{signal}: unavailable")

print("\nTest complete. No files were modified.")
