import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useData } from "../context/DataContext";
import { Globe2, Sparkles, FileText, CheckCircle2 } from "lucide-react";
import "./AnalysisReport.css";

export default function AnalysisReport() {
  const navigate = useNavigate();

  const {
    currentUser,
    pendingAnalysis,
    setPendingAnalysis,
    addSpeechResult,
  } = useData();

  const [speechName, setSpeechName] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const report = pendingAnalysis;

  const formatDuration = (seconds = 0) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    return `${minutes}m ${String(remainingSeconds).padStart(2, "0")}s`;
  };

  const handleSave = () => {
    const trimmedName = speechName.trim();

    if (!trimmedName) {
      setError("Please enter a name for your speech.");
      return;
    }

    const userKey = currentUser?.gmail || "default";

    if (!report) {
      setError("No analysis result found. Please analyse a video first.");
      return;
    }

    addSpeechResult(userKey, {
      ...report,
      title: trimmedName,
      date: report.date || new Date().toISOString().slice(0, 10),
    });

    setSaved(true);
    setPendingAnalysis(null);
  };

  if (!report && !saved) {
    return (
      <main className="analysis-report">
        <section className="report-empty" style={{ padding: "40px", textAlign: "center" }}>
          <h2>No analysis available</h2>
          <p style={{ margin: "14px 0 24px", color: "#91a0b5" }}>
            Upload a video and analyse your speech to see your report.
          </p>
          <button
            className="report-button report-button-primary"
            onClick={() => navigate("/upload")}
          >
            Go to Video Upload
          </button>
        </section>
      </main>
    );
  }

  if (saved) {
    return (
      <main className="analysis-report">
        <section className="report-success" style={{ padding: "40px", textAlign: "center" }}>
          <div className="success-icon" style={{ fontSize: "36px", color: "#68e694", marginBottom: "14px" }}>
            <CheckCircle2 size={44} style={{ display: "inline-block" }} />
          </div>
          <p className="report-eyebrow">REPORT SAVED</p>
          <h1>Speech saved successfully</h1>
          <p style={{ margin: "14px 0 24px", color: "#91a0b5" }}>
            Your report for <strong>{speechName.trim()}</strong> has been added to your progress.
          </p>

          <div className="report-actions" style={{ display: "flex", gap: "14px", justifyContent: "center" }}>
            <button
              className="report-button report-button-primary"
              onClick={() => navigate("/detailed-final")}
            >
              View my progress
            </button>

            <button
              className="report-button report-button-secondary"
              onClick={() => navigate("/upload")}
            >
              Analyse another video
            </button>
          </div>
        </section>
      </main>
    );
  }

  const deliveryScore = report.deliveryScore ?? report.score ?? 0;
  const vocalScore = report.vocalScore ?? report.score ?? 0;
  const bodyLanguageScore = report.bodyLanguageScore ?? report.score ?? 0;
  const coachingFeedback = report.coachingReport || report.feedback || "";
  const transcriptionText = report.transcription || report.transcript || "No transcription available.";
  const detectedAccent = report.detectedAccent || "Standard English";

  return (
    <main className="analysis-report">
      <header className="report-header">
        <div>
          <p className="report-eyebrow">ASTRA-HUNTERS / ANALYSIS</p>
          <h1>Speech Analysis Report</h1>
          <p className="report-subtitle">
            Multimodal AI Evaluation: Voice, Accent, Body Language & LLM Coaching.
          </p>
        </div>

        <span className="demo-badge" style={{ borderColor: "#4cd882", color: "#68e694" }}>
          AI EVALUATED
        </span>
      </header>

      <section className="speech-name-card">
        <label htmlFor="speechName">Name your speech</label>
        <p>Enter a title you'll recognise later in your progress history.</p>

        <input
          id="speechName"
          type="text"
          value={speechName}
          onChange={(event) => {
            setSpeechName(event.target.value);
            setError("");
          }}
          placeholder="e.g. Introduction to Artificial Intelligence"
          maxLength={100}
        />

        {error && <p className="report-error" style={{ color: "#f87171", marginTop: "8px" }}>{error}</p>}

        <button
          className="report-button report-button-primary save-report-button"
          onClick={handleSave}
          style={{ marginTop: "14px" }}
        >
          Save report
        </button>
      </section>

      {/* OVERALL SCORE */}
      <section className="report-score-card">
        <div>
          <p className="metric-label">OVERALL AI SCORE</p>
          <div className="overall-score">
            {report.score}
            <span>/100</span>
          </div>
          <p className="score-caption">Multimodal speaking grade</p>
        </div>

        <div className="score-ring">
          <span>{report.score}%</span>
          <small>Score</small>
        </div>
      </section>

      {/* THREE PREDICTED SCORES */}
      <section className="report-metrics" style={{ gridTemplateColumns: "repeat(3, minmax(0, 1fr))", marginTop: "20px" }}>
        <article className="metric-card">
          <span className="metric-label">DELIVERY SCORE</span>
          <strong>{deliveryScore}<small>/100</small></strong>
          <p>Confidence, pace & engagement</p>
        </article>

        <article className="metric-card">
          <span className="metric-label">VOCAL EXPRESSION</span>
          <strong>{vocalScore}<small>/100</small></strong>
          <p>Pitch dynamics & vocal range</p>
        </article>

        <article className="metric-card">
          <span className="metric-label">BODY LANGUAGE</span>
          <strong>{bodyLanguageScore}<small>/100</small></strong>
          <p>Posture & orientation</p>
        </article>
      </section>

      {/* DETECTED ACCENT */}
      <section className="report-panel" style={{ marginTop: "20px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <Globe2 size={24} color="#68e694" />
            <div>
              <h3 style={{ margin: 0, fontSize: "16px", color: "#f8fafc" }}>Detected Speaker Accent</h3>
              <p style={{ margin: "2px 0 0", color: "#91a0b5", fontSize: "13px" }}>
                Acoustic classification via Wav2Vec2 neural speech model
              </p>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ background: "#173d27", color: "#68e694", padding: "6px 16px", borderRadius: "999px", fontWeight: "700", border: "1px solid #43b76c" }}>
              {detectedAccent}
            </span>
            {report.accentConfidence && (
              <span style={{ color: "#91a0b5", fontSize: "12px" }}>({report.accentConfidence})</span>
            )}
          </div>
        </div>

        {report.presentationAccent && (
          <div
            style={{
              marginTop: "14px",
              padding: "12px 16px",
              background: "#0a111d",
              borderRadius: "8px",
              border: "1px solid #253246",
            }}
          >
            <p style={{ margin: "0 0 6px", fontSize: "12px", fontWeight: "600", color: "#68e694" }}>
              Classifier Output (output/audio_out/presentation_accent.txt):
            </p>
            <pre style={{ margin: 0, fontSize: "13px", color: "#e2e8f0", whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
              {report.presentationAccent}
            </pre>
          </div>
        )}
      </section>

      {/* SPEECH METRICS */}
      <section className="report-metrics" style={{ marginTop: "20px" }}>
        <article className="metric-card">
          <span className="metric-label">SPEAKING PACE</span>
          <strong>{report.pace || 0}</strong>
          <p>Words per minute</p>
        </article>

        <article className="metric-card">
          <span className="metric-label">DETECTED ACCENT</span>
          <strong style={{ color: "#68e694" }}>{detectedAccent}</strong>
          <p>{report.accentConfidence ? `Confidence: ${report.accentConfidence}` : "SpeechBrain Classifier"}</p>
        </article>

        <article className="metric-card">
          <span className="metric-label">FILLER WORDS</span>
          <strong>{report.fillerCount ?? 0}</strong>
          <p>Total detected</p>
        </article>

        <article className="metric-card">
          <span className="metric-label">PAUSES</span>
          <strong>{report.pauseCount ?? 0}</strong>
          <p>Deliberate pauses</p>
        </article>

        <article className="metric-card">
          <span className="metric-label">DURATION</span>
          <strong>{formatDuration(report.duration || 0)}</strong>
          <p>Speech duration</p>
        </article>

        <article className="metric-card">
          <span className="metric-label">AVERAGE PITCH</span>
          <strong>{report.averagePitch ? `${report.averagePitch} Hz` : "Analysed"}</strong>
          <p>Vocal frequency</p>
        </article>

        <article className="metric-card">
          <span className="metric-label">PITCH VARIATION</span>
          <strong>{report.pitchVariation || "Moderate"}</strong>
          <p>Intonation range</p>
        </article>
      </section>

      {/* AI COACHING REPORT */}
      <section className="report-panel" style={{ marginTop: "20px" }}>
        <h2 style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Sparkles size={20} color="#68e694" />
          AI Coaching Feedback
        </h2>
        <p className="panel-description">
          Automated executive coaching report generated by Groq LLM.
        </p>
        <div className="feedback-box" style={{ background: "#0a111d", padding: "18px", borderRadius: "8px", border: "1px solid #253246", marginTop: "12px" }}>
          <p style={{ margin: 0, lineHeight: 1.8, color: "#e2e8f0" }}>{coachingFeedback}</p>
        </div>
      </section>

      {/* TRANSCRIPT */}
      <section className="report-panel" style={{ marginTop: "20px" }}>
        <h2 style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <FileText size={20} color="#68e694" />
          Speech Transcription
        </h2>
        <p className="panel-description">
          Speech-to-text generated by Whisper neural transcription.
        </p>
        <div className="transcript-box" style={{ background: "#0a111d", padding: "18px", borderRadius: "8px", border: "1px solid #253246", marginTop: "12px", color: "#e2e8f0", lineHeight: 1.8 }}>
          {transcriptionText}
        </div>
      </section>

      <footer className="report-footer" style={{ marginTop: "30px", textAlign: "center", color: "#64748b", fontSize: "12px" }}>
        Astra-Hunters-2.0 Multimodal Public Speaking AI Platform
      </footer>
    </main>
  );
}