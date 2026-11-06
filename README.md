# 🎤 Astra-Hunters-2.0: Multimodal AI Presentation Evaluator

Astra-Hunters-2.0 is an end-to-end multimodal machine learning platform designed to automatically evaluate and coach human public speaking. By analyzing audio vocal dynamics and visual body language, the system maps human behavior to objective scores and generates personalized, LLM-driven feedback to help users improve their presentation skills.

## 🌟 Key Features

* **Multimodal Analysis:** Analyzes both audio (pitch, words per minute, pauses, filler words) and video (posture, hand gestures, screen presence) simultaneously.
* **Local Machine Learning Engine:** Utilizes a custom-trained Scikit-Learn Random Forest Regressor to predict human-level grades with ~75% accuracy (±9 point MAE).
* **AI Coaching Integration:** Seamlessly integrates with the Groq API (Llama 3.1) to translate raw numerical metrics into actionable, encouraging coaching paragraphs.
* **Modern Web Interface:** Features a React/Vite frontend connected to a lightning-fast FastAPI backend, allowing users to upload `.mp4` files and view dynamic performance dashboards.
* **Robust Fallback Systems:** The pipeline guarantees output; if the external LLM API fails or limits are reached, the system gracefully falls back to generating a local, rule-based text summary.

## 🏗️ System Architecture

The project operates on a procedural, script-based micro-architecture:

1. **Modality Separation (`video_separator.py`):** Uses FFmpeg to demultiplex `.wav` audio from the uploaded `.mp4` container.
2. **Audio Processing (`audio.py`, `detect_accent.py`):** Extracts sentence-by-sentence vocal metrics (WPM, Pitch Hz, Fillers) and identifies regional phonetic accents.
3. **Video Processing (`run_all_analysis.py`):** Utilizes Google MediaPipe to map a 33-point skeletal mesh and hand-tracking nodes on every frame to evaluate body language.
4. **Data Flattening (`flatten_audio.py`):** Condenses time-series data (multiple sentences) into a single mathematical 1D vector representing the entire presentation.
5. **AI Grading (`predict_scores.py`):** Feeds the flattened matrix into the serialized Random Forest model (`multimodal_model.joblib`) to predict scores for Delivery, Vocal Expression, and Body Language.
6. **LLM Coaching (`generate_coaching.py`):** Sends the extracted metrics to Groq's LLM to generate a personalized coaching report.

## 🛠️ Technology Stack

* **Backend / Pipeline:** Python, FastAPI, Uvicorn, Subprocess
* **Machine Learning:** Scikit-Learn, Pandas, Joblib
* **Computer Vision:** OpenCV, Google MediaPipe
* **Audio / NLP:** FFmpeg, Wav2Vec2 (Speech Processing)
* **LLM Integration:** Groq API (Llama Models)
* **Frontend:** React.js, Vite, Axios/Fetch

## 📊 Model Performance

Based on K-Fold Cross-Validation against our initial manually-graded dataset (N=41):
* **Delivery Score:** Accuracy ($R^2$): 0.75 | MAE: ±9.15
* **Vocal Expression:** Accuracy ($R^2$): 0.74 | MAE: ±8.87
* **Body Language:** Accuracy ($R^2$): 0.75 | MAE: ±9.10

## 🚀 Installation & Setup

### Prerequisites
* Python 3.9+
* Node.js & npm (for the frontend)
* **FFmpeg:** Must be installed on your system and added to your OS environment variables (PATH).

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Astra-Hunters-2.0.git
cd Astra-Hunters-2.0
```

### 2. Backend Setup
Create a virtual environment and install the required Python packages.
```bash
python -m venv .venv
# Activate environment (Windows)
.\.venv\Scripts\activate
# Activate environment (Mac/Linux)
source .venv/bin/activate

pip install -r requirements.txt
```
*(Note: Ensure `fastapi`, `uvicorn`, `python-multipart`, `groq`, `scikit-learn`, `pandas`, `mediapipe`, and `opencv-python` are in your requirements).*

### 3. Environment Variables
Create a `.env` file in the root directory and add your Groq API key:
```env
GROQ_API_KEY=gsk_your_api_key_here
```

### 4. Frontend Setup
Navigate to the frontend directory and install dependencies.
```bash
cd Astra-Frontend
npm install
```

## 🎮 Running the Application

For a fully integrated launch, run the backend and frontend simultaneously:

**Terminal 1 (Backend API):**
```bash
cd Astra-Hunters-2.0
.\.venv\Scripts\activate
uvicorn api:app --reload --port 8000
```

**Terminal 2 (Frontend UI):**
```bash
cd Astra-Hunters-2.0/Astra-Frontend
npm run dev
```
Open your browser to `http://localhost:5173` to upload a video and test the AI!

## 📂 Project Structure

```text
Astra-Hunters-2.0/
├── api.py                      # FastAPI server connecting React to the ML pipeline
├── run_pipeline.py             # Master orchestrator script
├── build_dataset.py            # Utility for batch processing training data
├── .env                        # Secure environment variables
├── data/
│   ├── raw/                    # Temporary storage for uploaded user videos
│   └── batch_videos/           # Storage for ML training datasets
├── output/                     # Generated JSON scores, text reports, and CSV datasets
├── src/                        # Core Machine Learning Pipeline
│   ├── audio/                  # Pitch, WPM, Filler word extraction & flattening
│   ├── preprocessing/          # FFmpeg video/audio separation
│   ├── training/               # Scripts to train the Scikit-Learn models
│   └── video/                  # MediaPipe posture and body language tracking
└── Astra-Frontend/             # React / Vite User Interface
    ├── src/
    ├── package.json
    └── vite.config.js
```

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! If you would like to improve the dataset, refine the Random Forest model, or add new tracking features (like eye-contact detection), feel free to fork the repository and submit a pull request.

## 📝 License
This project is licensed under the MIT License.
