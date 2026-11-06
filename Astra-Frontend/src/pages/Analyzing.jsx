
import { useData } from "../context/DataContext";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import "./Analyzing.css";

const API_BASE_URL = (
  import.meta.env.VITE_BACKEND_URL ||
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

function Analyzing() {
  const { currentUser, getUserProgress } = useData();

  const speeches = getUserProgress(currentUser?.gmail) || [];

  // 1. Sort speeches from oldest to newest.
  const sortedSpeeches = [...speeches].sort(
    (a, b) =>
      new Date(a.date || 0).getTime() -
      new Date(b.date || 0).getTime()
  );

  // 2. Improvement since the first speech.
  const firstScore =
    sortedSpeeches.length > 0 &&
    sortedSpeeches[0].score != null
      ? Number(sortedSpeeches[0].score)
      : null;

  const latestScore =
    sortedSpeeches.length > 0 &&
    sortedSpeeches[sortedSpeeches.length - 1].score != null
      ? Number(
          sortedSpeeches[sortedSpeeches.length - 1].score
        )
      : null;

  const improvement =
    firstScore !== null &&
    latestScore !== null &&
    Number.isFinite(firstScore) &&
    Number.isFinite(latestScore)
      ? latestScore - firstScore
      : null;

  // 3. Total speaking time.
  // Duration values must be stored in seconds.
  const totalSpeakingSeconds = speeches.reduce(
    (total, speech) => {
      const duration = Number(speech.duration);

      return (
        total +
        (Number.isFinite(duration) ? duration : 0)
      );
    },
    0
  );

  const formatDuration = (seconds) => {
    const total = Math.max(0, Math.round(seconds));
    const hours = Math.floor(total / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const remainingSeconds = total % 60;

    if (hours > 0) return `${hours}h ${minutes}m`;

    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }

    return `${remainingSeconds}s`;
  };

  // 4. Prepare graph data.
  const chartData = sortedSpeeches.map(
    (speech, index) => ({
      name: `Speech ${index + 1}`,
      score: Number(speech.score) || 0,
      title: speech.title || `Speech ${index + 1}`,
    })
  );

  // 5. Calculate average score.
  const scoredSpeeches = speeches.filter(
    (speech) =>
      speech.score != null &&
      Number.isFinite(Number(speech.score))
  );

  const averageScore =
    scoredSpeeches.length > 0
      ? Math.round(
          scoredSpeeches.reduce(
            (total, speech) =>
              total + Number(speech.score),
            0
          ) / scoredSpeeches.length
        )
      : 0;

  const getScoreLabel = (score) => {
    if (score >= 85) return "Excellent";
    if (score >= 70) return "Good";
    if (score >= 50) return "Needs improvement";

    return "Keep practising";
  };

  // 6. Download an individual speech report as PDF.
  async function downloadSpeechReport(speech) {
    const payload = {
      title: speech.title || "Speech report",
      date: speech.date || new Date().toISOString().slice(0, 10),
      score: speech.score ?? null,
      deliveryScore: speech.deliveryScore ?? null,
      vocalScore: speech.vocalScore ?? null,
      bodyLanguageScore: speech.bodyLanguageScore ?? null,
      detectedAccent: speech.detectedAccent || null,
      duration: speech.duration ?? null,
      pace: speech.pace ?? null,
      fillerCount: speech.fillerCount ?? speech.fillerWordsCount ?? null,
      pauseCount: speech.pauseCount ?? null,
      eyeContact: speech.eyeContact ?? null,
      posture: speech.posture ?? null,
      transcript: speech.transcript || "",
      drawbacks: speech.drawbacks || [],
      feedback: speech.feedback || "",
    };

    try {
      const response = await fetch(`${API_BASE_URL}/api/report/pdf`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(
          `Backend returned ${response.status}: Failed to generate PDF.`
        );
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");

      const cleanTitle = (speech.title || "speech-report")
        .toLowerCase()
        .replace(/[^a-z0-9_-]+/g, "-");
      link.href = url;
      link.download = `${cleanTitle}-report.pdf`;

      document.body.appendChild(link);
      link.click();
      link.remove();

      window.setTimeout(() => URL.revokeObjectURL(url), 2000);
    } catch (error) {
      console.warn(
        "Backend PDF generation unreachable or failed, falling back to print-to-PDF dialog:",
        error
      );
      // Client-side fallback: open a styled printable window for Save as PDF
      triggerClientPrintPdf(speech);
    }
  }

  function triggerClientPrintPdf(speech) {
    const title = speech.title || "Speech Analysis Report";
    const date = speech.date || new Date().toLocaleDateString();
    const score = speech.score != null ? `${speech.score}/100` : "N/A";
    const accent = speech.detectedAccent || "Standard English";
    const pace = speech.pace != null ? `${speech.pace} WPM` : "N/A";
    const fillers = speech.fillerCount ?? speech.fillerWordsCount ?? "0";
    const pauses = speech.pauseCount ?? "0";
    const duration = speech.duration != null ? formatDuration(speech.duration) : "N/A";
    const feedback = speech.feedback || "Speech evaluated successfully.";
    const transcript = speech.transcript || "No transcript available.";

    const printWin = window.open("", "_blank");
    if (!printWin) {
      alert("Pop-up blocked. Please allow pop-ups for this site to print or save your PDF report.");
      return;
    }

    printWin.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8" />
        <title>${title} - Astra-Hunters Report</title>
        <style>
          @page { size: A4; margin: 20mm; }
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #0f172a; margin: 0; padding: 20px; line-height: 1.5; }
          .header { border-bottom: 3px solid #68e694; padding-bottom: 12px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-end; }
          .brand { font-size: 20px; font-weight: 800; color: #0f172a; letter-spacing: 0.05em; }
          .subbrand { font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; }
          .title-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }
          .title-card h1 { margin: 0 0 6px 0; font-size: 22px; color: #0f172a; }
          .title-card p { margin: 0; color: #64748b; font-size: 13px; }
          .score-pill { background: #0f172a; color: #68e694; padding: 10px 18px; border-radius: 8px; text-align: center; }
          .score-pill strong { font-size: 24px; display: block; line-height: 1; }
          .score-pill span { font-size: 10px; color: #94a3b8; text-transform: uppercase; }
          .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
          .card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; }
          .card-label { font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 700; margin-bottom: 4px; }
          .card-value { font-size: 18px; font-weight: 800; color: #0f172a; }
          .section { margin-bottom: 24px; }
          .section-title { font-size: 14px; font-weight: 700; color: #0f172a; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin-bottom: 10px; }
          .feedback-text { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 14px; font-size: 14px; color: #166534; line-height: 1.6; }
          .transcript-text { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; font-size: 13px; color: #334155; line-height: 1.6; font-style: italic; }
          .footer { margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 12px; font-size: 11px; color: #94a3b8; text-align: center; }
        </style>
      </head>
      <body>
        <div class="header">
          <div>
            <div class="brand">ASTRA-HUNTERS 2.0</div>
            <div class="subbrand">Multimodal AI Public Speaking Evaluation Platform</div>
          </div>
          <div style="font-size: 12px; color: #64748b;">${date}</div>
        </div>

        <div class="title-card">
          <div>
            <h1>${title}</h1>
            <p>Speaker Accent: <strong>${accent}</strong> &bull; Recorded Performance Session</p>
          </div>
          <div class="score-pill">
            <strong>${score}</strong>
            <span>Overall Score</span>
          </div>
        </div>

        <div class="grid">
          <div class="card"><div class="card-label">Speaking Pace</div><div class="card-value">${pace}</div></div>
          <div class="card"><div class="card-label">Filler Words</div><div class="card-value">${fillers}</div></div>
          <div class="card"><div class="card-label">Pauses</div><div class="card-value">${pauses}</div></div>
          <div class="card"><div class="card-label">Duration</div><div class="card-value">${duration}</div></div>
        </div>

        <div class="section">
          <div class="section-title">AI Coaching Feedback</div>
          <div class="feedback-text">${feedback}</div>
        </div>

        <div class="section">
          <div class="section-title">Speech Transcript</div>
          <div class="transcript-text">${transcript}</div>
        </div>

        <div class="footer">
          Astra-Hunters-2.0 &bull; Automated Speech &amp; Presentation Analysis Report
        </div>

        <script>
          window.onload = function() {
            window.print();
          };
        </script>
      </body>
      </html>
    `);
    printWin.document.close();
  }

  // 7. Handle logged-out users.
  if (!currentUser) {
    return (
      <main className="progress-page">
        <div className="progress-empty">
          <h2>Please log in</h2>
          <p>Log in to view your speech progress.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="progress-page">
      <header className="progress-header">
        <div>
          <p className="progress-eyebrow">
            YOUR SPEAKING JOURNEY
          </p>

          <h1>{currentUser.name}'s Progress</h1>

          <p className="progress-subtitle">
            Welcome back, {currentUser.name}. Track your
            speaking performance and see how you improve
            with every speech.
          </p>
        </div>
      </header>

      {/* Summary cards */}
      <section className="progress-summary">
        <article className="summary-card">
          <span className="summary-label">
            Total speeches
          </span>

          <h2>{speeches.length}</h2>

          <p>Recorded sessions</p>
        </article>

        <article className="summary-card">
          <span className="summary-label">
            Average score
          </span>

          <h2>
            {scoredSpeeches.length
              ? `${averageScore}/100`
              : "--"}
          </h2>

          <p>Across all scored speeches</p>
        </article>

        <article className="summary-card">
          <span className="summary-label">
            Latest score
          </span>

          <h2>
            {latestScore !== null &&
            Number.isFinite(latestScore)
              ? `${latestScore}/100`
              : "--"}
          </h2>

          <p>Most recent session</p>
        </article>

        {/* NEW: Improvement since the first speech */}
        <article className="summary-card">
          <span className="summary-label">
            Improvement since first speech
          </span>

          <h2>
            {improvement === null
              ? "--"
              : `${improvement > 0 ? "+" : ""}${Number(
                  improvement.toFixed(1)
                )}`}
          </h2>

          <p>
            {improvement === null
              ? "Score data unavailable"
              : improvement > 0
                ? "Points gained since your first speech"
                : improvement < 0
                  ? "Points lower than your first speech"
                  : "Same score as your first speech"}
          </p>
        </article>

        {/* NEW: Total speaking time */}
        <article className="summary-card">
          <span className="summary-label">
            Total speaking time
          </span>

          <h2>
            {formatDuration(totalSpeakingSeconds)}
          </h2>

          <p>Across all analyzed speeches</p>
        </article>
      </section>

      {/* Score graph */}
      <section className="progress-panel">
        <div className="section-heading">
          <div>
            <h2>Score progression</h2>
            <p>
              Your score across each recorded speech
            </p>
          </div>
        </div>

        {chartData.length === 0 ? (
          <div className="progress-empty">
            <p>
              Your score graph will appear after your
              first speech analysis.
            </p>
          </div>
        ) : (
          <div className="progress-chart">
            <ResponsiveContainer
              width="100%"
              height={300}
            >
              <LineChart
                data={chartData}
                margin={{
                  top: 15,
                  right: 20,
                  left: 0,
                  bottom: 10,
                }}
              >
                <CartesianGrid
                  stroke="#e4e9e5"
                  strokeDasharray="4 4"
                  vertical={false}
                />

                <XAxis
                  dataKey="name"
                  tick={{
                    fill: "#647067",
                    fontSize: 12,
                  }}
                  axisLine={{
                    stroke: "#dce3dd",
                  }}
                  tickLine={false}
                />

                <YAxis
                  domain={[0, 100]}
                  ticks={[0, 20, 40, 60, 80, 100]}
                  tick={{
                    fill: "#647067",
                    fontSize: 12,
                  }}
                  axisLine={false}
                  tickLine={false}
                  width={38}
                />

                <Tooltip
                  contentStyle={{
                    borderRadius: "10px",
                    border: "1px solid #dce5dd",
                    backgroundColor: "#ffffff",
                  }}
                  formatter={(value) => [
                    `${value}/100`,
                    "Score",
                  ]}
                  labelFormatter={(label, payload) =>
                    payload?.[0]?.payload?.title || label
                  }
                />

                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#548b70"
                  strokeWidth={3}
                  dot={{
                    r: 5,
                    fill: "#548b70",
                    stroke: "#ffffff",
                    strokeWidth: 2,
                  }}
                  activeDot={{ r: 7 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      {/* Individual speech reports */}
      <section className="speech-history">
        <div className="section-heading">
          <div>
            <h2>All speech reports</h2>

            <p>
              Detailed performance reports for{" "}
              {currentUser.name}
            </p>
          </div>

          <span className="speech-count">
            {speeches.length}{" "}
            {speeches.length === 1
              ? "speech"
              : "speeches"}
          </span>
        </div>

        {sortedSpeeches.length === 0 ? (
          <div className="progress-empty">
            <h3>No speeches yet</h3>

            <p>
              Upload and analyse your first recording
              to see your report here.
            </p>
          </div>
        ) : (
          <div className="speech-list">
            {[...sortedSpeeches]
              .reverse()
              .map((speech) => (
                <article
                  className="speech-card"
                  key={speech.id}
                >
                  <div className="speech-card-header">
                    <div className="speech-title-group">
                      <span className="speech-icon">
                        S
                      </span>

                      <div>
                        <h3>
                          {speech.title ||
                            "Untitled speech"}
                        </h3>

                        <p>
                          {speech.date
                            ? new Date(
                                `${speech.date}T00:00:00`
                              ).toLocaleDateString(
                                "en-IN",
                                {
                                  day: "numeric",
                                  month: "short",
                                  year: "numeric",
                                }
                              )
                            : "Date unavailable"}
                        </p>
                      </div>
                    </div>

                    <div className="speech-score">
                      <strong>
                        {speech.score ?? "--"}
                      </strong>

                      <span>/100</span>

                      {speech.score != null && (
                        <small>
                          {getScoreLabel(
                            Number(speech.score)
                          )}
                        </small>
                      )}
                    </div>
                  </div>

                  {/* All available speech metrics */}
                  <div className="speech-metrics">
                    <div className="speech-metric">
                      <span>Speaking pace</span>

                      <strong>
                        {speech.pace != null
                          ? `${speech.pace} WPM`
                          : "Not available"}
                      </strong>
                    </div>

                    <div className="speech-metric">
                      <span>Filler words</span>

                      <strong>
                        {speech.fillerCount ??
                          speech.fillerWordsCount ??
                          "Not available"}
                      </strong>
                    </div>

                    <div className="speech-metric">
                      <span>Pauses</span>

                      <strong>
                        {speech.pauseCount ??
                          "Not available"}
                      </strong>
                    </div>

                    <div className="speech-metric">
                      <span>Duration</span>

                      <strong>
                        {speech.duration != null
                          ? typeof speech.duration ===
                            "number"
                            ? formatDuration(
                                speech.duration
                              )
                            : speech.duration
                          : "Not available"}
                      </strong>
                    </div>

                    <div className="speech-metric">
                      <span>Eye contact</span>

                      <strong>
                        {speech.eyeContact != null
                          ? typeof speech.eyeContact ===
                            "number"
                            ? `${speech.eyeContact}%`
                            : speech.eyeContact
                          : "Not available"}
                      </strong>
                    </div>

                    <div className="speech-metric">
                      <span>Posture</span>

                      <strong>
                        {speech.posture ??
                          "Not available"}
                      </strong>
                    </div>

                    {speech.detectedAccent && (
                      <div className="speech-metric">
                        <span>Accent</span>

                        <strong style={{ color: "#68e694" }}>
                          {speech.detectedAccent}
                        </strong>
                      </div>
                    )}
                  </div>

                  {/* Transcript */}
                  {speech.transcript && (
                    <div className="speech-detail">
                      <h4>Transcript</h4>

                      <p className="speech-transcript">
                        {speech.transcript}
                      </p>
                    </div>
                  )}

                  {/* Drawbacks */}
                  {Array.isArray(speech.drawbacks) &&
                    speech.drawbacks.length > 0 && (
                      <div className="speech-detail">
                        <h4>Areas to improve</h4>

                        <ul className="drawback-list">
                          {speech.drawbacks.map(
                            (drawback, index) => (
                              <li
                                key={`${speech.id}-${index}`}
                              >
                                {drawback}
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}

                  {/* Feedback */}
                  {speech.feedback && (
                    <div className="speech-detail">
                      <h4>Feedback</h4>
                      <p>{speech.feedback}</p>
                    </div>
                  )}

                  {/* PDF download button */}
                  <button
                    type="button"
                    onClick={() =>
                      downloadSpeechReport(speech)
                    }
                  >
                    Download Report as PDF
                  </button>
                </article>
              ))}
          </div>
        )}
      </section>
    </main>
  );
}

export default Analyzing;
