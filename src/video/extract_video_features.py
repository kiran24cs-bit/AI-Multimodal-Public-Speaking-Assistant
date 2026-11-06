#to make a single csv file for video features to be used in ML training in single row per video file
import pandas as pd
import json
import os
from pathlib import Path

def aggregate_video_features():
    video_out_dir = Path("output/video_out")
    facial_dir = video_out_dir / "facial_signal_reports"
    
    # Ensure it saves into the correct folder matching your structure
    ml_dataset_path = Path("output/video_ml_dataset/video_ml_dataset.csv")
    ml_dataset_path.parent.mkdir(parents=True, exist_ok=True)

    if not video_out_dir.exists():
        print("Error: video_out directory not found.")
        return

    try:
        latest_json = max(video_out_dir.glob("*_visual_analysis.json"), key=os.path.getctime)
        latest_csv = max(video_out_dir.glob("*_cleaned.csv"), key=os.path.getctime)
    except ValueError:
        print("Error: Could not find recent visual_analysis.json or cleaned.csv files.")
        return
        
    blinks_csv = facial_dir / "candidate_blinks.csv"

    features = {"video_file": "presentation.mp4"}

    # 1. Extract Blink Data
    if blinks_csv.exists():
        blinks_df = pd.read_csv(blinks_csv)
        features["total_blinks"] = len(blinks_df)
    else:
        features["total_blinks"] = 0

    # 2. Extract Movement Data using EXACT column names
    if latest_csv.exists():
        movement_df = pd.read_csv(latest_csv)
        
        if 'shoulder_tilt_normalized' in movement_df.columns:
            features["avg_shoulder_tilt"] = movement_df['shoulder_tilt_normalized'].mean()
            
        if 'torso_offset_normalized' in movement_df.columns:
            features["avg_torso_offset"] = movement_df['torso_offset_normalized'].mean()
            
        if 'left_wrist_displacement' in movement_df.columns:
            features["avg_left_wrist_movement"] = movement_df['left_wrist_displacement'].mean()
            
        if 'right_wrist_displacement' in movement_df.columns:
            features["avg_right_wrist_movement"] = movement_df['right_wrist_displacement'].mean()
            
        if 'hand_count' in movement_df.columns:
            features["avg_hands_visible"] = movement_df['hand_count'].mean()

    # 3. Extract Expression Data
    if latest_json.exists():
        with open(latest_json, 'r') as f:
            visual_data = json.load(f)
            intervals = visual_data.get("intervals", [])
            features["expression_changes"] = len(intervals)

    # 4. Save/Append to Master Video ML Dataset
    df = pd.DataFrame([features])
    file_exists = ml_dataset_path.exists()
    
    df.to_csv(ml_dataset_path, mode='a', header=not file_exists, index=False)
    print(f"\n Aggregated video features appended to: {ml_dataset_path.name}")
    print(df.to_string(index=False))

if __name__ == "__main__":
    aggregate_video_features()