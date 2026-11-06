import pandas as pd
import joblib
import json
from pathlib import Path

def predict_new_video():
    output_dir = Path("output")
    
    model_path = output_dir / "multimodal_model.joblib"
    features_path = output_dir / "model_features.joblib"
    
    audio_path = output_dir / "audio_ml_dataset" / "flattened_audio_dataset.csv"
    video_path = output_dir / "video_ml_dataset" / "video_ml_dataset.csv"
    
    # 1. Verify model exists
    if not model_path.exists():
        print(" Error: Trained model not found. Please run train_model.py first.")
        return

    # 2. Load the trained brain and expected feature column list
    model = joblib.load(model_path)
    expected_features = joblib.load(features_path)
    
    # 3. Read the latest audio and video feature entries (last row)
    audio_df = pd.read_csv(audio_path)
    video_df = pd.read_csv(video_path)
    
    latest_audio = audio_df.iloc[[-1]].copy()
    latest_video = video_df.iloc[[-1]].copy()
    
    # Standardize stem names for merging
    latest_audio['base_name'] = latest_audio['audio_file'].apply(lambda x: str(Path(x).stem))
    latest_video['base_name'] = latest_video['video_file'].apply(lambda x: str(Path(x).stem))
    
    # 4. Merge audio and video features for the new video
    merged_data = pd.merge(latest_audio, latest_video, on='base_name', how='inner')
    
    if merged_data.empty:
        print(" Error: Could not match audio and video data for the newest video.")
        return
        
    video_name = merged_data['base_name'].iloc[0]
    
    # 5. Ensure feature columns align perfectly with what the model expects
    for col in expected_features:
        if col not in merged_data.columns:
            merged_data[col] = 0
            
    X_predict = merged_data[expected_features]
    
    # 6. Predict scores using the trained model
    print(f"Predicting scores for: {video_name}...")
    predictions = model.predict(X_predict)[0]
    
    results = {
        "video_analyzed": video_name,
        "predicted_scores": {
            "Delivery Score": round(float(predictions[0]), 1),
            "Vocal Expression": round(float(predictions[1]), 1),
            "Body Language": round(float(predictions[2]), 1)
        }
    }
    
    # 7. Save predicted scores to JSON for down-stream processing (e.g., Gemini feedback)
    results_path = output_dir / "final_predicted_scores.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=4)
        
    print("\n" + "="*50)
    print("PREDICTION COMPLETE!")
    for category, score in results["predicted_scores"].items():
        print(f"   • {category}: {score}/100")
    print(f"Results saved to: {results_path.resolve()}")
    print("="*50 + "\n")
    import subprocess

# ... existing predict_scores.py code ...

    print("\n Final predicted scores saved to output/final_predicted_scores.json")
    
    import sys
    subprocess.run([sys.executable, "src/generate_coaching.py"])

if __name__ == "__main__":
    predict_new_video()