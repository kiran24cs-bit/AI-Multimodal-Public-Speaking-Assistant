
import csv
import json
import glob
import os
from pathlib import Path

import matplotlib.pyplot as plt

# Find the latest visual-analysis JSON.
files = glob.glob("output/video_out/*visual_analysis.json")

if not files:
    raise FileNotFoundError(
        "No visual-analysis JSON found in output/video_out/"
    )

json_path = max(files, key=os.path.getmtime)

with open(json_path, "r", encoding="utf-8") as file:
    data = json.load(file)

rows = []

for frame in data.get("frames", []):
    face = frame.get("face", {})
    shapes = face.get("blendshapes", {})

    rows.append({
        "timestamp_seconds": frame["timestamp_seconds"],
        "face_detected": face.get("detected", False),
        "eyeBlinkLeft": shapes.get("eyeBlinkLeft"),
        "eyeBlinkRight": shapes.get("eyeBlinkRight"),
        "jawOpen": shapes.get("jawOpen"),
        "mouthSmileLeft": shapes.get("mouthSmileLeft"),
        "mouthSmileRight": shapes.get("mouthSmileRight"),
    })

output_dir = Path("output/video_out/facial_signal_reports")
output_dir.mkdir(parents=True, exist_ok=True)

csv_path = output_dir / "facial_signals.csv"

with open(csv_path, "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

# Plot the existing measurements.
face_rows = [r for r in rows if r["face_detected"]]

times = [r["timestamp_seconds"] for r in face_rows]
left = [r["eyeBlinkLeft"] for r in face_rows]
right = [r["eyeBlinkRight"] for r in face_rows]
jaw = [r["jawOpen"] for r in face_rows]

fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

axes[0].plot(times, left, label="Left eye blink score")
axes[0].plot(times, right, label="Right eye blink score")
axes[0].set_ylabel("Blendshape score")
axes[0].set_title("Eye-blink signals over time")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].plot(times, jaw, label="Jaw open score")
axes[1].set_xlabel("Video timestamp (seconds)")
axes[1].set_ylabel("Blendshape score")
axes[1].set_title("Jaw-opening signal over time")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()

chart_path = output_dir / "facial_signals.png"
plt.savefig(chart_path, dpi=150)
plt.close()

print("Source JSON:", json_path)
print("Frames exported:", len(rows))
print("CSV report:", csv_path)
print("Signal chart:", chart_path)
print("Original JSON was not modified.")
