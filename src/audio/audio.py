import re
import json
from pathlib import Path
from collections import Counter

import whisper
import librosa
import numpy as np
import pandas as pd


# ============================================================
# 1. CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Point to the processed audio file in the data folder
AUDIO_FILE = PROJECT_ROOT / "data" / "processed" / "presentation.wav"
MODEL_NAME = "base"
PAUSE_THRESHOLD = 0.30

# Point to the standard output folder for the project
OUTPUT_DIR = PROJECT_ROOT / "output"/"audio_out"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILLERS = [
    "you know",
    "i mean",
    "i guess",
    "kind of",
    "sort of",
    "um",
    "uh",
    "uhh",
    "umm",
    "erm",
    "er",
    "hmm",
    "hm",
    "ah",
    "actually",
    "basically",
    "literally",
]

# Longer phrases are checked first.
FILLER_PATTERN = re.compile(
    r"\b(?:"
    + "|".join(
        re.escape(f) for f in sorted(FILLERS, key=len, reverse=True)
    )
    + r")\b",
    re.IGNORECASE,
)


def rounded(value, digits=3):
    """Round a numeric value, preserving missing values."""
    if value is None or not np.isfinite(value):
        return None
    return round(float(value), digits)


def count_fillers(text):
    """Return individual filler counts from recognized text."""
    return Counter(
        match.group(0).lower()
        for match in FILLER_PATTERN.finditer(text)
    )


def get_pitch(audio_clip, sample_rate):
    """
    Estimate sentence pitch using YIN.
    Values are fundamental frequency estimates in Hz.
    """
    empty = {
        "pitch_mean_hz": None,
        "pitch_median_hz": None,
        "pitch_min_hz": None,
        "pitch_max_hz": None,
        "pitch_std_hz": None,
        "voiced_pitch_frame_count": 0,
    }

    if len(audio_clip) < int(0.10 * sample_rate):
        return empty

    clip = audio_clip - np.mean(audio_clip)

    if np.sqrt(np.mean(clip ** 2)) < 1e-4:
        return empty

    try:
        f0 = librosa.yin(
            clip,
            fmin=65,
            fmax=500,
            sr=sample_rate,
            frame_length=2048,
            hop_length=256,
        )

        valid = f0[
            np.isfinite(f0) & (f0 >= 65) & (f0 <= 500)
        ]

        if len(valid) == 0:
            return empty

        return {
            "pitch_mean_hz": rounded(np.mean(valid), 2),
            "pitch_median_hz": rounded(np.median(valid), 2),
            "pitch_min_hz": rounded(np.min(valid), 2),
            "pitch_max_hz": rounded(np.max(valid), 2),
            "pitch_std_hz": rounded(np.std(valid), 2),
            "voiced_pitch_frame_count": int(len(valid)),
        }

    except Exception:
        return empty


# ============================================================
# 2. VALIDATE AND LOAD AUDIO
# ============================================================

audio_path = Path(AUDIO_FILE)

if not audio_path.exists():
    raise FileNotFoundError(
        f"Audio file not found: {audio_path.resolve()}\n"
        f"Please ensure 'presentation.wav' exists in the 'data/processed/' folder."
    )

print("Loading audio...")

audio, sample_rate = librosa.load(
    str(audio_path),
    sr=16000,
    mono=True,
)

duration = len(audio) / sample_rate

print("Loading Whisper model...")
model = whisper.load_model(MODEL_NAME)


# ============================================================
# 3. TRANSCRIBE AUDIO
# ============================================================

print("Transcribing audio...")

result = model.transcribe(
    str(audio_path),
    language="en",
    fp16=False,
    temperature=0,
    word_timestamps=True,
    initial_prompt=(
        "Transcribe the speech as accurately as possible. "
        "Preserve filler words, hesitations, repetitions, "
        "false starts, and disfluencies. Do not intentionally "
        "remove words such as um, uh, hmm, you know, like, "
        "actually, basically, and I mean."
    ),
)

transcript = result["text"].strip()

# Save transcription separately.
transcript_path = OUTPUT_DIR / "transcription.txt"
transcript_path.write_text(transcript, encoding="utf-8")

print("Transcription saved.")


# ============================================================
# 4. EXTRACT WORD TIMESTAMPS
# ============================================================

words = []

for segment in result.get("segments", []):
    for item in segment.get("words", []):
        word_text = item.get("word", "").strip()

        if not word_text:
            continue

        start = max(
            0.0,
            min(float(item.get("start", segment["start"]),), duration),
        )
        end = max(
            start,
            min(float(item.get("end", segment["end"])), duration),
        )

        words.append({
            "word": word_text,
            "start": start,
            "end": end,
        })

words.sort(key=lambda x: (x["start"], x["end"]))


# ============================================================
# 5. DETECT PAUSES BETWEEN ALIGNED WORDS
# ============================================================

pauses = []

for previous, current in zip(words, words[1:]):
    gap = current["start"] - previous["end"]

    if gap >= PAUSE_THRESHOLD:
        pauses.append({
            "pause_start_seconds": rounded(previous["end"]),
            "pause_end_seconds": rounded(current["start"]),
            "pause_duration_seconds": rounded(gap),
            "word_before_pause": previous["word"],
            "word_after_pause": current["word"],
        })

total_pause_duration = sum(
    p["pause_duration_seconds"] for p in pauses
)

speech_active_duration = max(
    0.0, duration - total_pause_duration
)


# ============================================================
# 6. OVERALL RECORDING FEATURES
# ============================================================

total_words = len(words)
overall_fillers = count_fillers(transcript)
total_fillers = sum(overall_fillers.values())

overall_wpm = (
    total_words / duration * 60 if duration > 0 else 0.0
)

active_wpm = (
    total_words / speech_active_duration * 60
    if speech_active_duration > 0 else 0.0
)

filler_frequency = (
    total_fillers / total_words * 100
    if total_words > 0 else 0.0
)

most_used_filler = (
    overall_fillers.most_common(1)[0][0]
    if overall_fillers else "None"
)

# JSON string columns preserve detailed event information
# while keeping the dataset in one CSV file.
all_pauses_json = json.dumps(pauses, ensure_ascii=False)
filler_counts_json = json.dumps(
    dict(overall_fillers), ensure_ascii=False
)


# ============================================================
# 7. SPLIT ALIGNED WORDS INTO SENTENCES
# ============================================================

sentences = []
current_words = []

for word in words:
    current_words.append(word)

    if re.search(r'[.!?]["\')\]]*$', word["word"]):
        sentences.append(current_words)
        current_words = []

if current_words:
    sentences.append(current_words)

# Fallback for empty word-level alignment.
if not sentences and result.get("segments"):
    for segment in result["segments"]:
        segment_text = segment.get("text", "").strip()

        if segment_text:
            sentences.append([{
                "word": segment_text,
                "start": float(segment["start"]),
                "end": float(segment["end"]),
            }])


# ============================================================
# 8. BUILD ONE ROW PER SENTENCE
# ============================================================

rows = []

for sentence_number, sentence_words in enumerate(sentences, start=1):

    sentence_text = " ".join(
        item["word"] for item in sentence_words
    ).strip()

    sentence_start = sentence_words[0]["start"]
    sentence_end = sentence_words[-1]["end"]
    sentence_duration = max(0.0, sentence_end - sentence_start)

    sentence_word_count = sum(
        len(re.findall(r"\b[\w'-]+\b", item["word"]))
        for item in sentence_words
    )

    sentence_wpm = (
        sentence_word_count / sentence_duration * 60
        if sentence_duration > 0 else 0.0
    )

    # Filler features for this sentence.
    sentence_fillers = count_fillers(sentence_text)
    sentence_filler_total = sum(sentence_fillers.values())

    # Pauses with both neighboring words inside this sentence.
    sentence_pauses = []

    for previous, current in zip(
        sentence_words, sentence_words[1:]
    ):
        gap = current["start"] - previous["end"]

        if gap >= PAUSE_THRESHOLD:
            sentence_pauses.append({
                "start_seconds": rounded(previous["end"]),
                "end_seconds": rounded(current["start"]),
                "duration_seconds": rounded(gap),
                "word_before": previous["word"],
                "word_after": current["word"],
            })

    sentence_pause_durations = [
        p["duration_seconds"] for p in sentence_pauses
    ]

    sentence_pause_total = sum(sentence_pause_durations)

    # Audio pitch features for this sentence.
    start_sample = max(
        0, int(sentence_start * sample_rate)
    )
    end_sample = min(
        len(audio), int(sentence_end * sample_rate)
    )

    pitch = get_pitch(
        audio[start_sample:end_sample],
        sample_rate,
    )

    # Pauses immediately before and after this sentence.
    preceding_pauses = [
        p for p in pauses
        if abs(p["pause_end_seconds"] - sentence_start) <= 0.10
    ]

    following_pauses = [
        p for p in pauses
        if abs(p["pause_start_seconds"] - sentence_end) <= 0.10
    ]

    pause_before = (
        preceding_pauses[-1]["pause_duration_seconds"]
        if preceding_pauses else 0.0
    )

    pause_after = (
        following_pauses[0]["pause_duration_seconds"]
        if following_pauses else 0.0
    )

    row = {
        # Recording identification
        "audio_file": audio_path.name,
        "sentence_number": sentence_number,

        # Overall recording features (repeated per sentence)
        "audio_duration_seconds": rounded(duration),
        "audio_duration_minutes": rounded(duration / 60),
        "recording_total_words": total_words,
        "recording_overall_wpm": rounded(overall_wpm, 2),
        "recording_active_wpm": rounded(active_wpm, 2),
        "recording_total_fillers": total_fillers,
        "recording_filler_frequency_percent": rounded(
            filler_frequency, 2
        ),
        "recording_most_used_filler": most_used_filler,
        "recording_filler_counts_json": filler_counts_json,
        "recording_total_pauses": len(pauses),
        "recording_total_pause_seconds": rounded(
            total_pause_duration
        ),
        "recording_active_seconds_estimate": rounded(
            speech_active_duration
        ),
        "pause_threshold_seconds": PAUSE_THRESHOLD,

        # Sentence text and timestamps
        "sentence_text": sentence_text,
        "sentence_start_seconds": rounded(sentence_start),
        "sentence_end_seconds": rounded(sentence_end),
        "sentence_duration_seconds": rounded(sentence_duration),
        "sentence_word_count": sentence_word_count,
        "sentence_wpm": rounded(sentence_wpm, 2),

        # Sentence-level fillers
        "sentence_total_fillers": sentence_filler_total,
        "sentence_filler_counts_json": json.dumps(
            dict(sentence_fillers), ensure_ascii=False
        ),

        # Sentence-level pauses
        "sentence_pause_count": len(sentence_pauses),
        "sentence_total_pause_seconds": rounded(
            sentence_pause_total
        ),
        "sentence_mean_pause_seconds": rounded(
            np.mean(sentence_pause_durations)
            if sentence_pause_durations else 0.0
        ),
        "sentence_longest_pause_seconds": rounded(
            max(sentence_pause_durations)
            if sentence_pause_durations else 0.0
        ),
        "pause_before_sentence_seconds": rounded(pause_before),
        "pause_after_sentence_seconds": rounded(pause_after),
        "sentence_pause_events_json": json.dumps(
            sentence_pauses, ensure_ascii=False
        ),

        # Overall pause event details, retained in every row
        "recording_pause_events_json": all_pauses_json,

        # Sentence pitch
        **pitch,
    }

    rows.append(row)


# ============================================================
# 9. SAVE THE CONSOLIDATED ML DATASET
# ============================================================

csv_path = OUTPUT_DIR / "speech_ml_dataset.csv"

columns = [
    "audio_file",
    "sentence_number",
    "audio_duration_seconds",
    "audio_duration_minutes",
    "recording_total_words",
    "recording_overall_wpm",
    "recording_active_wpm",
    "recording_total_fillers",
    "recording_filler_frequency_percent",
    "recording_most_used_filler",
    "recording_filler_counts_json",
    "recording_total_pauses",
    "recording_total_pause_seconds",
    "recording_active_seconds_estimate",
    "pause_threshold_seconds",
    "sentence_text",
    "sentence_start_seconds",
    "sentence_end_seconds",
    "sentence_duration_seconds",
    "sentence_word_count",
    "sentence_wpm",
    "sentence_total_fillers",
    "sentence_filler_counts_json",
    "sentence_pause_count",
    "sentence_total_pause_seconds",
    "sentence_mean_pause_seconds",
    "sentence_longest_pause_seconds",
    "pause_before_sentence_seconds",
    "pause_after_sentence_seconds",
    "sentence_pause_events_json",
    "recording_pause_events_json",
    "pitch_mean_hz",
    "pitch_median_hz",
    "pitch_min_hz",
    "pitch_max_hz",
    "pitch_std_hz",
    "voiced_pitch_frame_count",
]

df = pd.DataFrame(rows, columns=columns)

# Keep an empty recording from crashing the export.
df.to_csv(csv_path, index=False, encoding="utf-8-sig")


# ============================================================
# 10. PRINT SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("           SPEECH ANALYSIS COMPLETED")
print("=" * 60)

print(f"Duration:          {duration:.2f} seconds")
print(f"Words:             {total_words}")
print(f"Overall WPM:       {overall_wpm:.2f}")
print(f"Estimated active WPM: {active_wpm:.2f}")
print(f"Total fillers:     {total_fillers}")
print(f"Most-used filler:  {most_used_filler}")
print(f"Total pauses:      {len(pauses)}")
print(f"Sentence count:    {len(rows)}")
print(f"CSV columns:       {len(columns)}")

print("\nFiller breakdown:")
for filler, count in overall_fillers.most_common():
    print(f"  {filler}: {count}")

print("\nSaved files:")
print(f"  ML dataset:   {csv_path.resolve()}")
print(f"  Transcription: {transcript_path.resolve()}")

print("\nCSV rows:", len(df))
print("CSV columns:", len(df.columns))
print("=" * 60)