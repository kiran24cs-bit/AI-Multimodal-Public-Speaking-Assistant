import pandas as pd
from pathlib import Path

def merge_datasets():
    # 1. Define paths matching your exact folder structure
    output_dir = Path("output")
    
    audio_path = output_dir / "audio_ml_dataset" / "flattened_audio_dataset.csv"
    video_path = output_dir / "video_ml_dataset" / "video_ml_dataset.csv"
    labels_path = output_dir / "human_labels.csv" 
    
    # Verify files exist before attempting to load
    missing = [p.name for p in [audio_path, video_path, labels_path] if not p.exists()]
    if missing:
        print(f" Error: Missing required files for fusion: {', '.join(missing)}")
        print("Please ensure you have flattened the audio and created human_labels.csv.")
        return
        
    print("Loading datasets...")
    audio_df = pd.read_csv(audio_path)
    video_df = pd.read_csv(video_path)
    labels_df = pd.read_csv(labels_path)
    
    # 2. Standardize a 'base_name' column to merge on (removes .wav and .mp4)
    # This assumes your columns are named 'audio_file', 'video_file', and 'file_name'
    if 'audio_file' in audio_df.columns:
        audio_df['base_name'] = audio_df['audio_file'].apply(lambda x: str(Path(x).stem))
    else:
        print(" Error: 'audio_file' column missing from flattened_audio_dataset.csv")
        return
        
    if 'video_file' in video_df.columns:
        video_df['base_name'] = video_df['video_file'].apply(lambda x: str(Path(x).stem))
    else:
        print(" Error: 'video_file' column missing from video_ml_dataset.csv")
        return
        
    if 'file_name' in labels_df.columns:
        labels_df['base_name'] = labels_df['file_name'].apply(lambda x: str(Path(x).stem))
    else:
        print(" Error: 'file_name' column missing from human_labels.csv")
        return
    
    # 3. Merge Audio and Video features
    print("Fusing Audio and Video features...")
    merged_features = pd.merge(audio_df, video_df, on='base_name', how='inner')
    
    # 4. Merge features with Human Labels
    print("Attaching Human Labels...")
    final_dataset = pd.merge(merged_features, labels_df, on='base_name', how='inner')
    
    # 5. Clean up redundant columns
    columns_to_drop = ['audio_file', 'video_file', 'file_name']
    final_dataset = final_dataset.drop(columns=[col for col in columns_to_drop if col in final_dataset.columns])
    
    # Move 'base_name' and 'speaker_id' to the front for readability
    cols = final_dataset.columns.tolist()
    if 'base_name' in cols:
        cols.insert(0, cols.pop(cols.index('base_name')))
    if 'speaker_id' in cols:
        cols.insert(1, cols.pop(cols.index('speaker_id')))
    final_dataset = final_dataset[cols]
    
    # 6. Save the master dataset for training
    final_path = output_dir / "multimodal_training_dataset.csv"
    final_dataset.to_csv(final_path, index=False)
    
    print("\n" + "="*60)
    print(f" MULTIMODAL FUSION COMPLETE ")
    print(f"Master dataset saved to: {final_path.resolve()}")
    print(f"Total merged presentations ready for training: {len(final_dataset)}")
    print("="*60 + "\n")

if __name__ == "__main__":
    merge_datasets()