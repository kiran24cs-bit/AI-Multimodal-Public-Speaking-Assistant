import pandas as pd
from pathlib import Path

def flatten_audio_data():
    input_path = Path("output/audio_out/speech_ml_dataset.csv")
    output_path = Path("output/audio_ml_dataset/flattened_audio_dataset.csv")
    
    if not input_path.exists():
        print(f" Error: {input_path.resolve()} not found.")
        return
        
    print("Loading multi-row audio dataset...")
    df = pd.read_csv(input_path)
    
    print("Flattening data into one row per audio file...")
    aggregation_rules = {
        'recording_total_words': 'first',
        'recording_overall_wpm': 'first',
        'recording_active_wpm': 'first',
        'recording_total_fillers': 'first',
        'recording_filler_frequency_percent': 'first',
        'recording_total_pauses': 'first',
        'recording_total_pause_seconds': 'first',
        'recording_active_seconds_estimate': 'first',
        'pitch_mean_hz': 'mean',
        'pitch_median_hz': 'mean',
        'pitch_std_hz': 'mean'
    }
    
    aggregation_rules = {k: v for k, v in aggregation_rules.items() if k in df.columns}
    
    flattened_df = df.groupby('audio_file').agg(aggregation_rules).reset_index()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # If the flattened CSV exists, combine existing rows with new rows
    if output_path.exists():
        existing_df = pd.read_csv(output_path)
        combined_df = pd.concat([existing_df, flattened_df], ignore_index=True)
        # Drop duplicates based on audio_file, keeping the newest entry
        final_df = combined_df.drop_duplicates(subset=['audio_file'], keep='last')
    else:
        final_df = flattened_df
    
    final_df.to_csv(output_path, index=False)
    
    print(f" Success! Flattened audio data saved to: {output_path.name}")
    print(f"Total presentations logged in flattened dataset: {len(final_df)}")

if __name__ == "__main__":
    flatten_audio_data()