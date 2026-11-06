import shutil
import subprocess
import sys
import pandas as pd
from pathlib import Path

def main():
    print(" BATCH DATASET BUILDER ")
    
    batch_dir = Path("data/batch_videos")
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    videos = list(batch_dir.glob("*.mp4"))
    if not videos:
        print(f" No videos found! Please drop your training MP4s into: {batch_dir.resolve()}")
        return
        
    print(f"Found {len(videos)} videos to process.\n")
    target_video = Path("data/raw/presentation.mp4")
    
    audio_csv_path = Path("output/audio_ml_dataset/speech_ml_dataset.csv")
    video_csv_path = Path("output/video_ml_dataset/video_ml_dataset.csv")
    flattened_csv_path = Path("output/audio_ml_dataset/flattened_audio_dataset.csv")
    
    for index, video_path in enumerate(videos, start=1):
        print(f"\n{'='*60}")
        print(f" PROCESSING VIDEO {index}/{len(videos)}: {video_path.name}")
        print(f"{'='*60}")
        
        # 1. Temporarily copy and rename the video
        target_video.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(video_path, target_video)
        
        # 2. Run the pipeline (which now includes flatten_audio.py)
        try:
            subprocess.run([sys.executable, "run_pipeline.py"], check=True)
        except subprocess.CalledProcessError:
            print(f" Pipeline failed for {video_path.name}. Skipping to next video...")
            continue
            
        # 3. Patch Audio CSV
        if audio_csv_path.exists():
            df_audio = pd.read_csv(audio_csv_path)
            mask = df_audio['audio_file'].astype(str).str.contains('presentation', case=False, na=False)
            if mask.any():
                df_audio.loc[mask, 'audio_file'] = video_path.stem + ".wav"
                df_audio.to_csv(audio_csv_path, index=False)
                
        # 4. Patch Video CSV
        if video_csv_path.exists():
            df_video = pd.read_csv(video_csv_path)
            mask = df_video['video_file'].astype(str).str.contains('presentation', case=False, na=False)
            if mask.any():
                df_video.loc[mask, 'video_file'] = video_path.stem + ".mp4"
                df_video.to_csv(video_csv_path, index=False)

        # 5. Patch the Flattened Audio CSV
        if flattened_csv_path.exists():
            df_flat = pd.read_csv(flattened_csv_path)
            mask_flat = df_flat['audio_file'].astype(str).str.contains('presentation', case=False, na=False)
            if mask_flat.any():
                df_flat.loc[mask_flat, 'audio_file'] = video_path.stem + ".wav"
                df_flat.to_csv(flattened_csv_path, index=False)
                
        print(f" Real name '{video_path.stem}' safely logged to all datasets.")
                
    print("\n ALL VIDEOS PROCESSED! Your datasets are ready for training.")

if __name__ == "__main__":
    main()