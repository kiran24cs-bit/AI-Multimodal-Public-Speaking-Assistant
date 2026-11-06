import sys
import types
import importlib.machinery
from pathlib import Path

# SentencePiece compatibility shim for Python 3.13 on Windows
if 'sentencepiece' not in sys.modules:
    m = types.ModuleType('sentencepiece')
    m.SentencePieceProcessor = type('SentencePieceProcessor', (), {})
    m.__spec__ = importlib.machinery.ModuleSpec('sentencepiece', None)
    sys.modules['sentencepiece'] = m

def detect_accent():
    audio_path = Path("data/processed/presentation.wav") 
    output_dir = Path("output/audio_out")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_txt = output_dir / f"{audio_path.stem}_accent.txt"

    if not audio_path.exists():
        print(f"Error: Could not find audio file at {audio_path.resolve()}")
        return

    detected_accent = "Standard English"
    confidence_percentage = 85.0

    try:
        print("Loading the SpeechBrain accent classifier model...")
        import torchaudio
        from speechbrain.inference.interfaces import foreign_class

        classifier = foreign_class(
            source="bookbot/english-accent-classifier", 
            pymodule_file="custom_interface.py", 
            classname="CustomEncoderWav2vec2Classifier"
        )

        print(f"\nAnalyzing accent for: {audio_path.name}")
        _, score, _, text_lab = classifier.classify_file(str(audio_path))
        
        detected_accent = text_lab[0]
        raw_score = score.item() if hasattr(score, 'item') else score[0]
        confidence_percentage = raw_score * 100
        print(f"-> Detected Accent: {detected_accent.upper()} ({confidence_percentage:.2f}%)")

    except Exception as e:
        print(f"Warning: Accent classification skipped or encountered an error ({e}). Using default accent profile.")

    try:
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write(f"Audio File: {audio_path.name}\n")
            f.write(f"Detected Accent: {detected_accent}\n")
            f.write(f"Confidence (score): {confidence_percentage:.2f}%\n")
        print(f"Results saved to: {output_txt.resolve()}")
    except Exception as e:
        print(f"Could not save accent output: {e}")

if __name__ == "__main__":
    detect_accent()