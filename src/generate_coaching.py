import json
import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("GROQ_API_KEY")

def generate_feedback():
    scores_path = Path("output/final_predicted_scores.json")
    audio_path = Path("output/audio_ml_dataset/flattened_audio_dataset.csv")
    
    if not scores_path.exists() or not audio_path.exists():
        print(" Error: Missing predicted scores or audio dataset.")
        return

    # 1. Load the AI predicted scores
    with open(scores_path, "r") as f:
        data = json.load(f)
        scores = data.get("predicted_scores", {})

    # 2. Load the specific raw metrics for this video
    df_audio = pd.read_csv(audio_path)
    latest_audio = df_audio.iloc[-1]
    
    wpm = latest_audio.get('recording_overall_wpm', 0)
    fillers = latest_audio.get('recording_total_fillers', 0)
    pauses = latest_audio.get('recording_total_pauses', 0)
    pitch_var = latest_audio.get('pitch_std_hz', 0)

    feedback = ""

    # 3. Try Groq API first
    if API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=API_KEY)
            
            prompt = f"""
            You are an expert public speaking coach. Your client just gave a presentation. 
            Here are the AI-graded scores (out of 100):
            - Delivery: {scores.get('Delivery Score', 0):.1f}
            - Vocal Expression: {scores.get('Vocal Expression', 0):.1f}
            - Body Language: {scores.get('Body Language', 0):.1f}

            Here are their raw metrics:
            - Speaking Pace: {wpm:.1f} Words Per Minute.
            - Filler Words Used: {fillers}
            - Total Pauses: {pauses}
            - Pitch Variance: {pitch_var:.1f} Hz.

            Write a short, encouraging 3-4 sentence coaching summary pointing out strengths and areas to practice.
            """

            print(f"\n{'='*60}")
            print(" GENERATING GROQ AI COACHING FEEDBACK...")
            print(f"{'='*60}\n")

            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a direct, professional, and encouraging executive speaking coach."
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="openai/gpt-oss-120b",
                temperature=0.7,
                max_tokens=256,
        )
            feedback = chat_completion.choices[0].message.content
        except Exception as e:
            print(f" Groq API warning ({e}). Falling back to local metric summary...")

    # 4. Fallback rule-based summary if API is skipped or fails
    if not feedback:
        feedback = (
            f"Performance Summary:\n"
            f"- Delivery: {scores.get('Delivery Score', 0):.1f}/100 | Vocal Expression: {scores.get('Vocal Expression', 0):.1f}/100 | Body Language: {scores.get('Body Language', 0):.1f}/100.\n"
            f"- Pacing: {wpm:.1f} WPM with {fillers} filler words detected.\n"
            f"- Recommendation: Focus on maintaining steady pacing and minimizing filler sounds during transitions."
        )

    print(" COACHING REPORT:\n")
    print(feedback)
    print(f"\n{'='*60}")

# 5. Save the LLM feedback text file for Streamlit with UTF-8 encoding
    with open("output/coaching_report.txt", "w", encoding="utf-8") as out_file:
        out_file.write(feedback)

if __name__ == "__main__":
    generate_feedback()