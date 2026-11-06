import pandas as pd
from pathlib import Path
import numpy as np

def prepare():
    output_dir = Path("output"/"audio_out")
    output_dir.mkdir(exist_ok=True)
    
    audio_features_path = output_dir / "audio_ml_dataset" / "speech_ml_dataset.csv"
    labels_path = output_dir / "human_labels.csv"
    final_training_path = output_dir / "training_dataset.csv"

    if not audio_features_path.exists():
        print(f"Error: {audio_features_path} not found. Run your audio extraction first.")
        return

    print("Loading audio features...")
    df_audio = pd.read_csv(audio_features_path)

    # 1. Aggregate sentence-level data to presentation-level
    print("Aggregating features...")
    aggregation_rules = {
        # Overall recording stats (take the first value since they repeat per sentence)
        'audio_duration_seconds': 'first',
        'recording_total_words': 'first',
        'recording_overall_wpm': 'first',
        'recording_active_wpm': 'first',
        'recording_total_fillers': 'first',
        'recording_filler_frequency_percent': 'first',
        'recording_total_pauses': 'first',
        'recording_total_pause_seconds': 'first',
        
        # Sentence-level stats (calculate the average across the whole presentation)
        'sentence_wpm': 'mean',
        'sentence_total_fillers': 'mean',
        'sentence_mean_pause_seconds': 'mean',
        'pitch_mean_hz': 'mean',
        'pitch_median_hz': 'mean',
        'pitch_std_hz': 'mean',
    }

    # Group by audio file and apply the rules
    df_presentation = df_audio.groupby('audio_file').agg(aggregation_rules).reset_index()

    # Rename averaged columns for clarity
    df_presentation.rename(columns={
        'sentence_wpm': 'avg_sentence_wpm',
        'sentence_total_fillers': 'avg_sentence_fillers',
        'sentence_mean_pause_seconds': 'avg_sentence_pause_sec',
        'pitch_mean_hz': 'avg_pitch_mean_hz',
        'pitch_median_hz': 'avg_pitch_median_hz',
        'pitch_std_hz': 'avg_pitch_std_hz'
    }, inplace=True)

    # 2. Handle Human Labels
    if not labels_path.exists():
        print(f"\n[ATTENTION] Creating scoring template at: {labels_path}")
        df_labels = pd.DataFrame({
            'audio_file': df_presentation['audio_file'].unique(),
            'delivery_score': [np.nan] * len(df_presentation),
            'vocal_expression_score': [np.nan] * len(df_presentation),
            'body_language_score': [np.nan] * len(df_presentation)
        })
        df_labels.to_csv(labels_path, index=False)
        print("-> Please open 'output/human_labels.csv', type in scores (0-100), and run this script again.")
        return
    
    df_labels = pd.read_csv(labels_path)
    if df_labels['delivery_score'].isna().all():
        print("\n[ATTENTION] 'human_labels.csv' is empty. Please fill in the 0-100 scores and run again.")
        return

    # 3. Merge features and labels
    df_final = pd.merge(df_presentation, df_labels, on='audio_file', how='inner')
    df_final.dropna(subset=['delivery_score', 'vocal_expression_score', 'body_language_score'], inplace=True)

    if df_final.empty:
        print("Error: Merged dataset is empty. Ensure 'audio_file' names match in both CSVs.")
        return

    # 4. Save Final ML Dataset
    df_final.to_csv(final_training_path, index=False)
    print(f"\nSUCCESS! ML training dataset saved to: {final_training_path}")
    print(f"Total labeled presentations ready: {len(df_final)}")
    print(f"Numeric features extracted: {len(df_final.columns) - 4}") # -4 for filename and 3 targets

if __name__ == "__main__":
    prepare()