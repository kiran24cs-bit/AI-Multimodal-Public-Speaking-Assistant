import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Upload,
  Video,
  RefreshCw,
  ArrowRight,
  FileVideo2,
  ShieldCheck,
  Save,
  CheckCircle2,
  Sparkles,
  Award,
  Globe2,
  FileText,
  AlertTriangle,
} from "lucide-react";
import { useData } from "../context/DataContext";
import "./UploadVideo.css";

const MAX_FILE_SIZE_MB = 500;
const API_BASE_URL = (
  import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

const PIPELINE_STAGES = [
  { at: 0, text: "Uploading presentation to Astra-Hunters backend..." },
  { at: 6, text: "Separating audio and video streams..." },
  { at: 15, text: "Extracting acoustic features (Pitch, Pauses, WPM)..." },
  { at: 28, text: "Classifying speaker accent with Wav2Vec2..." },
  { at: 42, text: "Analyzing body language, facial orientation & posture..." },
  { at: 55, text: "Aggregating multimodal features & computing AI grades..." },
  { at: 65, text: "Synthesizing expert coaching report with Groq LLM..." },
];

export default function UploadVideo() {
  const inputRef = useRef(null);
  const navigate = useNavigate();

  const { currentUser, addSpeechResult, setPendingAnalysis } = useData();

  const [videoFile, setVideoFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState("");
  const [videoDuration, setVideoDuration] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [progressStage, setProgressStage] = useState("");
  const [report, setReport] = useState(null);
  const [speechName, setSpeechName] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  // Revoke object URL on unmount or file change
  useEffect(() => {
    return () => {
      if (videoUrl) URL.revokeObjectURL(videoUrl);
    };
  }, [videoUrl]);

  // Dynamic progress stage update based on elapsed seconds
  useEffect(() => {
    let interval = null;
    if (isAnalyzing) {
      setProgressStage(PIPELINE_STAGES[0].text);
      interval = setInterval(() => {
        setElapsedSeconds((prev) => {
          const next = prev + 1;
          const currentStage = [...PIPELINE_STAGES]
            .reverse()
            .find((stage) => next >= stage.at);
          if (currentStage) {
            setProgressStage(currentStage.text);
          }
          return next;
        });
      }, 1000);
    } else {
      setElapsedSeconds(0);
      setProgressStage("");
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isAnalyzing]);

  function selectVideo(file) {
    setError("");

    if (!file) return;

    if (!file.type.startsWith("video/") && !file.name.match(/\.(mp4|webm|mov|m4v)$/i)) {
      setError("Please choose a valid video file (MP4, WebM, or MOV).");
      return;
    }

    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setError(`Choose a video smaller than ${MAX_FILE_SIZE_MB} MB.`);
      return;
    }

    const nextUrl = URL.createObjectURL(file);

    setVideoFile(file);
    setVideoUrl(nextUrl);
    setVideoDuration(0);
    setReport(null);
    setSpeechName(file.name.replace(/\.[^/.]+$/, ""));
    setSaved(false);
  }

  function handleInputChange(event) {
    selectVideo(event.target.files?.[0]);
    event.target.value = "";
  }

  function handleDrop(event) {
    event.preventDefault();
    selectVideo(event.dataTransfer.files?.[0]);
  }

  async function startAnalysis() {
    if (!videoFile || isAnalyzing) return;

    setError("");
    setReport(null);
    setSaved(false);
    setIsAnalyzing(true);

    const formData = new FormData();
    formData.append("file", videoFile);

    try {
      const response = await fetch(`${API_BASE_URL}/analyze-video`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorDetail =
          data.detail ||
          data.error ||
          `Server returned HTTP ${response.status}: ${response.statusText}`;
        throw new Error(errorDetail);
      }

      // Map backend response
      const predictedScores = data.predicted_scores || {};
      const scores = data.scores || {};
      const metrics = data.metrics || {};

      const delivery = Number(
        scores.delivery ?? predictedScores["Delivery Score"] ?? 0
      );
      const vocal = Number(
        scores.vocal ?? predictedScores["Vocal Expression"] ?? 0
      );
      const bodyLanguage = Number(
        scores.body_language ?? predictedScores["Body Language"] ?? 0
      );
      const overall = Number(
        scores.overall ?? Math.round((delivery + vocal + bodyLanguage) / 3)
      );

      const generatedReport = {
        date: new Date().toISOString().slice(0, 10),
        score: overall,
        deliveryScore: delivery,
        vocalScore: vocal,
        bodyLanguageScore: bodyLanguage,
        detectedAccent: data.detected_accent || "Standard English",
        accentConfidence: data.accent_confidence || "",
        presentationAccent: data.presentation_accent || "",
        coachingReport:
          data.coaching_report ||
          "Analysis complete. Continue practicing to maintain dynamic vocal range.",
        transcription:
          data.transcription || "No transcription generated for this recording.",
        duration: metrics.duration || Math.round(videoDuration || 0),
        pace: metrics.pace || 0,
        fillerCount: metrics.fillerCount || 0,
        pauseCount: metrics.pauseCount || 0,
        averagePitch: metrics.averagePitch || 0,
        pitchVariation: metrics.pitchVariation || "Moderate",
        posture: bodyLanguage >= 80 ? "Confident & Upright" : "Moderate",
        feedback: data.coaching_report || "",
      };

      setReport(generatedReport);
      setPendingAnalysis(generatedReport);
    } catch (err) {
      console.error("Analysis request failed:", err);
      let userFriendlyMessage = err.message || "Failed to process video.";
      if (
        userFriendlyMessage.includes("Failed to fetch") ||
        userFriendlyMessage.includes("NetworkError")
      ) {
        userFriendlyMessage = `Could not connect to the backend server at ${API_BASE_URL}. Please ensure the FastAPI server is running (e.g. uvicorn api:app --port 8000).`;
      }
      setError(userFriendlyMessage);
    } finally {
      setIsAnalyzing(false);
    }
  }

  function saveReport() {
    const userKey = currentUser?.gmail || "default";

    if (!report) {
      setError("No analysis result is available to save.");
      return;
    }

    if (!speechName.trim()) {
      setError("Please enter a name for your speech.");
      return;
    }

    addSpeechResult(userKey, {
      ...report,
      title: speechName.trim(),
    });

    setSaved(true);
    setError("");
  }

  function resetAnalysis() {
    setReport(null);
    setSaved(false);
    setError("");
  }

  return (
    <section className="upload-page">
      <div className="upload-page-heading">
        <span className="upload-eyebrow">
          <span className="upload-eyebrow-dot" />
          MULTIMODAL AI EVALUATION STUDIO
        </span>

        <h1>Speech & Video Analysis</h1>
        <p>
          Upload your presentation recording to evaluate Delivery, Vocal Expression,
          Body Language, Accent, and receive AI coaching recommendations.
        </p>
      </div>

      {!videoFile ? (
        <div
          className="upload-dropzone"
          role="button"
          tabIndex={0}
          aria-label="Choose a video to upload"
          onClick={() => inputRef.current?.click()}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              inputRef.current?.click();
            }
          }}
          onDragOver={(event) => event.preventDefault()}
          onDrop={handleDrop}
        >
          <input
            ref={inputRef}
            className="upload-hidden-input"
            type="file"
            accept="video/*,.mp4,.webm,.mov,.m4v"
            onChange={handleInputChange}
          />

          <div className="upload-icon-orbit" aria-hidden="true">
            <div className="upload-icon-circle">
              <Upload size={34} strokeWidth={1.7} />
            </div>
            <span className="upload-orbit-dot upload-orbit-dot-one" />
            <span className="upload-orbit-dot upload-orbit-dot-two" />
          </div>

          <h2>Drop your video here</h2>
          <p className="upload-dropzone-copy">
            or click below to browse files from your device
          </p>

          <button
            className="upload-choose-button"
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              inputRef.current?.click();
            }}
          >
            <FileVideo2 size={18} /> Choose Video
          </button>

          <p className="upload-file-hint">
            MP4, WebM or MOV · Up to  30 Second
          </p>
        </div>
      ) : (
        <div className="upload-preview-card">
          <div className="upload-preview-topline">
            <div className="upload-preview-file-icon">
              <Video size={19} />
            </div>

            <div className="upload-preview-file-info">
              <h2 title={videoFile.name}>{videoFile.name}</h2>
              <p>
                {formatFileSize(videoFile.size)} · Ready to analyse
                {videoDuration > 0 && ` (${formatDuration(videoDuration)})`}
              </p>
            </div>

            <span className="upload-ready-label">
              <span /> Video ready
            </span>
          </div>

          <div className="upload-video-frame">
            <video
              key={videoUrl}
              src={videoUrl}
              controls
              playsInline
              preload="metadata"
              onLoadedMetadata={(event) => {
                const duration = event.currentTarget.duration;
                if (Number.isFinite(duration)) {
                  setVideoDuration(duration);
                }
              }}
              aria-label={`Preview of ${videoFile.name}`}
            >
              Your browser does not support video playback.
            </video>
          </div>

          <div className="upload-preview-actions">
            <button
              type="button"
              className="upload-change-button"
              onClick={() => inputRef.current?.click()}
              disabled={isAnalyzing}
            >
              <RefreshCw size={17} /> Change Video
            </button>

            <input
              ref={inputRef}
              className="upload-hidden-input"
              type="file"
              accept="video/*,.mp4,.webm,.mov,.m4v"
              onChange={handleInputChange}
            />

            <button
              type="button"
              className="upload-analyze-button"
              onClick={startAnalysis}
              disabled={isAnalyzing}
            >
              {isAnalyzing ? "Analysing Pipeline..." : "Start Analysis"}
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {isAnalyzing && (
        <div className="upload-analysis-state" role="status">
          <div className="upload-loader" />
          <div className="upload-progress-info">
            <span className="upload-progress-timer">{elapsedSeconds}s</span>
            <div className="upload-progress-stage">{progressStage}</div>
            <p className="upload-progress-subtext">
              The multimodal neural models & Wav2Vec2 classifier take approx. 45–60
              seconds to analyze video posture, acoustics, and accent.
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="upload-error" role="alert">
          <AlertTriangle
            size={18}
            style={{ display: "inline-block", marginRight: "8px", verticalAlign: "middle" }}
          />
          <strong>Error: </strong>
          <span>{error}</span>
        </div>
      )}

      {report && !isAnalyzing && (
        <div className="speech-report">
          <div className="speech-report-heading">
            <span className="upload-eyebrow">ASTRA-HUNTERS MULTIMODAL REPORT</span>
            <h2>Evaluation Results</h2>
            <p>
              AI-generated speech and body language evaluation for{" "}
              <strong>{videoFile?.name}</strong>.
            </p>
          </div>

          {/* 1. THREE CORE PREDICTED SCORES + OVERALL */}
          <div className="speech-scores-grid">
            <div className="speech-score-card is-highlight">
              <span>Overall Score</span>
              <strong>
                {report.score}
                <small>/100</small>
              </strong>
              <p>Combined AI Assessment</p>
            </div>

            <div className="speech-score-card">
              <span>Delivery Score</span>
              <strong>
                {report.deliveryScore}
                <small>/100</small>
              </strong>
              <p>Clarity, engagement & flow</p>
            </div>

            <div className="speech-score-card">
              <span>Vocal Expression</span>
              <strong>
                {report.vocalScore}
                <small>/100</small>
              </strong>
              <p>Pitch dynamics & speech cadence</p>
            </div>

            <div className="speech-score-card">
              <span>Body Language</span>
              <strong>
                {report.bodyLanguageScore}
                <small>/100</small>
              </strong>
              <p>Posture, orientation & gestures</p>
            </div>
          </div>

          {/* 2. DETECTED ACCENT BANNER */}
          <div className="speech-accent-banner">
            <div className="speech-accent-info">
              <Globe2 size={20} color="#68e694" />
              <span className="speech-accent-label">Detected Speaker Accent:</span>
              <span className="speech-accent-tag">{report.detectedAccent}</span>
              {report.accentConfidence && (
                <span className="speech-accent-confidence">
                  (Confidence: {report.accentConfidence})
                </span>
              )}
            </div>
            <span className="upload-eyebrow">Wav2Vec2 SpeechBrain Model</span>
          </div>

          {report.presentationAccent && (
            <div
              className="speech-accent-raw-card"
              style={{
                marginTop: "10px",
                marginBottom: "20px",
                padding: "12px 16px",
                borderRadius: "8px",
                background: "rgba(104, 230, 148, 0.08)",
                border: "1px solid rgba(104, 230, 148, 0.25)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <span style={{ fontSize: "12px", fontWeight: "700", color: "#68e694", letterSpacing: "0.05em" }}>
                  ACCENT CLASSIFIER DETAILS (output/audio_out/presentation_accent.txt)
                </span>
                <span style={{ fontSize: "11px", color: "#91a0b5" }}>Wav2Vec2 Speech Classifier</span>
              </div>
              <pre
                style={{
                  margin: 0,
                  fontSize: "13px",
                  lineHeight: "1.6",
                  color: "#e2e8f0",
                  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                  whiteSpace: "pre-wrap",
                }}
              >
                {report.presentationAccent}
              </pre>
            </div>
          )}

          {/* 3. COACHING REPORT (GROQ LLM) */}
          <div className="speech-report-section">
            <h3 style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Sparkles size={19} color="#68e694" />
              AI Coaching Feedback
            </h3>
            <p className="speech-feedback">{report.coachingReport}</p>
          </div>

          {/* 4. SPEECH TRANSCRIPTION (WHISPER) */}
          <div className="speech-report-section">
            <h3 style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <FileText size={19} color="#68e694" />
              Speech Transcription
            </h3>
            <p className="speech-transcript">{report.transcription}</p>
          </div>

          {/* 5. ACOUSTIC & PHYSICAL METRICS */}
          <div className="speech-report-section">
            <h3>Extracted Performance Metrics</h3>
            <div className="speech-metrics-grid">
              <Metric label="Speaking Pace" value={`${report.pace} WPM`} />
              <Metric label="Filler Words Detected" value={report.fillerCount} />
              <Metric label="Speech Pauses" value={report.pauseCount} />
              <Metric label="Duration" value={formatDuration(report.duration)} />
              <Metric
                label="Average Pitch"
                value={report.averagePitch > 0 ? `${report.averagePitch} Hz` : "Detected"}
              />
              <Metric label="Detected Accent" value={report.detectedAccent} />
              <Metric label="Pitch Variation" value={report.pitchVariation} />
            </div>
          </div>

          {/* 6. SAVE SESSION PANEL */}
          {!saved ? (
            <div className="speech-save-panel">
              <label htmlFor="speech-name">Name your presentation</label>
              <input
                id="speech-name"
                type="text"
                value={speechName}
                onChange={(event) => setSpeechName(event.target.value)}
                placeholder="e.g. Q4 Executive Strategy Pitch"
                maxLength={100}
              />

              <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                <button
                  type="button"
                  className="speech-save-button"
                  onClick={saveReport}
                >
                  <Save size={18} /> Save to Progress
                </button>
                <button
                  type="button"
                  className="upload-change-button"
                  onClick={() => navigate("/report")}
                >
                  View Full Report Page <ArrowRight size={16} />
                </button>
              </div>
            </div>
          ) : (
            <div className="speech-saved-message" role="status">
              <CheckCircle2 size={22} />
              <div>
                <strong>Analysis saved successfully!</strong>
                <p>“{speechName.trim()}” has been recorded into your progress history.</p>
              </div>
            </div>
          )}

          <div style={{ marginTop: "24px", display: "flex", gap: "12px" }}>
            <button
              type="button"
              className="upload-change-button"
              onClick={resetAnalysis}
            >
              Analyse another video
            </button>
          </div>
        </div>
      )}

      <div className="upload-privacy-note">
        <span className="upload-privacy-icon">
          <ShieldCheck size={19} />
        </span>
        <span>
          <strong>Automated Multimodal Pipeline.</strong>
          <small>
            Your video is processed securely by the local Astra-Hunters ML engine,
            extracting posture, acoustic frequencies, and speech dynamics.
          </small>
        </span>
      </div>
    </section>
  );
}

function Metric({ label, value }) {
  return (
    <div className="speech-metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatFileSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  return `${minutes}:${String(remainingSeconds).padStart(2, "0")}`;
}
