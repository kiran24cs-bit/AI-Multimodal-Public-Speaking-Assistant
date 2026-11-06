import { useEffect, useRef, useState } from "react";
import "./Practice.css";


function estimatePitch(buffer, sampleRate) {
  // Lightweight autocorrelation pitch estimate. Returns Hz, or null for silence/noisy frames.
  let rms = 0;
  for (let i = 0; i < buffer.length; i++) rms += buffer[i] * buffer[i];
  rms = Math.sqrt(rms / buffer.length);
  if (rms < 0.012) return null;

  let bestOffset = -1;
  let bestCorrelation = 0;
  const minHz = 70;
  const maxHz = 350;
  const minOffset = Math.floor(sampleRate / maxHz);
  const maxOffset = Math.min(
    Math.floor(sampleRate / minHz),
    buffer.length - 1
  );

  for (let offset = minOffset; offset <= maxOffset; offset++) {
    let correlation = 0;
    const limit = buffer.length - offset;
    for (let i = 0; i < limit; i++) {
      correlation += buffer[i] * buffer[i + offset];
    }
    correlation /= limit;

    if (correlation > bestCorrelation) {
      bestCorrelation = correlation;
      bestOffset = offset;
    }
  }

  if (bestOffset < 0 || bestCorrelation < 0.01) return null;
  return Math.round(sampleRate / bestOffset);
}

function formatTime(totalSeconds) {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
}

export default function Practice() {
  const [status, setStatus] = useState("idle");
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [waveBars, setWaveBars] = useState(Array(36).fill(5));
  const [pitchPoints, setPitchPoints] = useState([]);
  const [currentPitch, setCurrentPitch] = useState(null);
  const [averagePitch, setAveragePitch] = useState(null);
  const [pauseMessage, setPauseMessage] = useState("");
  const [pauseCount, setPauseCount] = useState(0);
  const [error, setError] = useState("");
  const [summary, setSummary] = useState(null);
  const [isPaused, setIsPaused] = useState(false);

  const activeRef = useRef(false);
  const recognitionRef = useRef(null);
  const recognitionRetryRef = useRef(null);
  const recognitionSupportedRef = useRef(false);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationRef = useRef(null);
  const startedAtRef = useRef(0);
  const silenceStartedRef = useRef(null);
  const pauseShownRef = useRef(false);
  const pitchSamplesRef = useRef([]);
  const finalTranscriptRef = useRef("");
  const interimTranscriptRef = useRef("");
  const pauseCountRef = useRef(0);
  const latestPitchRef = useRef(null);
  const pitchIntervalRef = useRef(null);
  const pausedRef = useRef(false);
  const elapsedBeforePauseRef = useRef(0);

  useEffect(() => {
    return () => {
      activeRef.current = false;
      if (recognitionRetryRef.current) clearTimeout(recognitionRetryRef.current);
      if (recognitionRef.current) {
        recognitionRef.current.onend = null;
        try {
          recognitionRef.current.stop();
        } catch {}
      }
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      if (pitchIntervalRef.current) clearInterval(pitchIntervalRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => {});
      }
    };
  }, []);

  function setupSpeechRecognition() {
    const SpeechRecognitionAPI =
      typeof window !== "undefined"
        ? window.SpeechRecognition || window.webkitSpeechRecognition
        : null;

    if (!SpeechRecognitionAPI) {
      setError(
        "Live transcription is not available in this browser. Open this page in the latest Google Chrome. Pitch and microphone features can still work."
      );
      return;
    }

    recognitionSupportedRef.current = true;
    const recognition = new SpeechRecognitionAPI();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    // en-IN is not enabled reliably on every browser speech service; en-US is a
    // more widely supported fallback if the selected locale returns no results.
    recognition.lang = "en-IN";

    recognition.onstart = () => {
      setError("");
    };

    recognition.onresult = (event) => {
      // Append only newly-finalized results. Keep interim words visible immediately.
      // Rebuilding all results can lose text when Chrome restarts its recognition service.
      let newFinalText = "";
      let currentInterimText = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const spokenText = result?.[0]?.transcript?.trim();
        if (!spokenText) continue;
        if (result.isFinal) newFinalText += `${spokenText} `;
        else currentInterimText += `${spokenText} `;
      }

      if (newFinalText.trim()) {
        finalTranscriptRef.current = `${finalTranscriptRef.current} ${newFinalText}`
          .replace(/\s+/g, " ")
          .trim();
      }
      interimTranscriptRef.current = currentInterimText.trim();
      setTranscript(finalTranscriptRef.current);
      setInterimTranscript(interimTranscriptRef.current);
    };

    recognition.onerror = (event) => {
      const code = event?.error || "unknown";
      if (code === "not-allowed" || code === "service-not-allowed") {
        setError("Chrome blocked speech recognition. Click the site icon near the address bar, allow microphone access, then reload the page.");
      } else if (code === "network") {
        setError("Speech-to-text needs an internet connection in Chrome. Check your connection and start a new practice session.");
      } else if (code === "audio-capture") {
        setError("Chrome cannot access the microphone for speech recognition. Check your microphone and close other apps using it.");
      } else if (code !== "no-speech" && code !== "aborted") {
        setError(`Speech-to-text error (${code}). Try refreshing the page in Google Chrome.`);
      }
    };

    recognition.onend = () => {
      if (!activeRef.current || pausedRef.current) return;
      // Chrome can end a continuous recognition session after silence. Restart it
      // after a short delay instead of immediately (immediate restarts can be ignored).
      if (recognitionRetryRef.current) clearTimeout(recognitionRetryRef.current);
      recognitionRetryRef.current = setTimeout(() => {
        if (!activeRef.current || pausedRef.current) return;
        try {
          recognition.start();
        } catch {
          // If Chrome is still transitioning, onend will schedule the next retry.
        }
      }, 300);
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
    } catch (err) {
      setError(`Could not start speech-to-text (${err?.message || "browser blocked it"}). Try refreshing in Google Chrome.`);
    }
  }

  async function startPractice() {
    setError("");
    setSummary(null);
    setIsPaused(false);
    pausedRef.current = false;
    elapsedBeforePauseRef.current = 0;
    latestPitchRef.current = null;
    setTranscript("");
    setInterimTranscript("");
    setElapsed(0);
    setWaveBars(Array(36).fill(5));
    setPitchPoints([]);
    setCurrentPitch(null);
    setAveragePitch(null);
    setPauseMessage("");
    setPauseCount(0);
    pitchSamplesRef.current = [];
    finalTranscriptRef.current = "";
    interimTranscriptRef.current = "";
    pauseCountRef.current = 0;
    silenceStartedRef.current = null;
    pauseShownRef.current = false;

    try {
      if (recognitionRetryRef.current) clearTimeout(recognitionRetryRef.current);
      if (recognitionRef.current) {
        recognitionRef.current.onend = null;
        try { recognitionRef.current.abort(); } catch {}
        recognitionRef.current = null;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const AudioContextAPI = window.AudioContext || window.webkitAudioContext;
      const audioContext = new AudioContextAPI();
      audioContextRef.current = audioContext;
      await audioContext.resume();

      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 2048;
      analyser.smoothingTimeConstant = 0.65;
      source.connect(analyser);
      analyserRef.current = analyser;

      activeRef.current = true;
      startedAtRef.current = Date.now();
      setStatus("recording");
      setupSpeechRecognition();

      const buffer = new Float32Array(analyser.fftSize);

      const updateAudio = () => {
        if (!activeRef.current || !analyserRef.current || pausedRef.current) return;

        analyserRef.current.getFloatTimeDomainData(buffer);

        let sumSquares = 0;
        for (let i = 0; i < buffer.length; i++) {
          sumSquares += buffer[i] * buffer[i];
        }
        const rms = Math.sqrt(sumSquares / buffer.length);
        const level = Math.min(100, Math.round(rms * 420));
        setWaveBars((previous) => [
          ...previous.slice(1),
          Math.max(4, level),
        ]);

        const pitch = estimatePitch(buffer, audioContext.sampleRate);

        if (rms < 0.012) {
          if (silenceStartedRef.current === null) {
            silenceStartedRef.current = Date.now();
          }

          const silenceDuration = Date.now() - silenceStartedRef.current;
          if (silenceDuration >= 1500 && !pauseShownRef.current) {
            pauseShownRef.current = true;
            pauseCountRef.current += 1;
            setPauseCount(pauseCountRef.current);
            setPauseMessage("You paused speaking. Continue when you're ready.");
          }
        } else {
          silenceStartedRef.current = null;
          pauseShownRef.current = false;
          setPauseMessage("");
        }

        if (pitch !== null && rms >= 0.012) {
          latestPitchRef.current = pitch;
          setCurrentPitch(pitch);
        } else {
          latestPitchRef.current = null;
          setCurrentPitch(null);
        }

        setElapsed(elapsedBeforePauseRef.current + Math.floor((Date.now() - startedAtRef.current) / 1000));
        animationRef.current = requestAnimationFrame(updateAudio);
      };

      animationRef.current = requestAnimationFrame(updateAudio);
      // Store one pitch sample every two seconds instead of plotting every audio frame.
      let pitchWindow = [];
      pitchIntervalRef.current = setInterval(() => {
        if (!activeRef.current || pausedRef.current) return;
        const voicedWindow = pitchWindow.filter((value) => Number.isFinite(value));
        const sample = voicedWindow.length
          ? Math.round(voicedWindow.reduce((sum, value) => sum + value, 0) / voicedWindow.length)
          : null;
        pitchSamplesRef.current.push(sample);
        setPitchPoints([...pitchSamplesRef.current]);
        const allVoiced = pitchSamplesRef.current.filter((value) => Number.isFinite(value));
        setAveragePitch(allVoiced.length ? Math.round(allVoiced.reduce((sum, value) => sum + value, 0) / allVoiced.length) : null);
        pitchWindow = [];
      }, 2000);
      // The live analyser feeds the 2-second pitch window.
      const samplePitch = () => {
        if (!activeRef.current || pausedRef.current || !analyserRef.current) return;
        if (latestPitchRef.current !== null) pitchWindow.push(latestPitchRef.current);
        requestAnimationFrame(samplePitch);
      };
      requestAnimationFrame(samplePitch);
    } catch (err) {
      activeRef.current = false;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
      if (audioContextRef.current) {
        await audioContextRef.current.close().catch(() => {});
        audioContextRef.current = null;
      }
      setStatus("idle");
      setError(
        err.name === "NotAllowedError"
          ? "Microphone access was blocked. Allow it in your browser and try again."
          : err.message || "Could not start microphone recording."
      );
    }
  }

  async function endPractice() {
    if (!activeRef.current) return;

    activeRef.current = false;
    pausedRef.current = false;
    setIsPaused(false);
    setStatus("finished");

    if (animationRef.current) cancelAnimationFrame(animationRef.current);
    if (pitchIntervalRef.current) clearInterval(pitchIntervalRef.current);

    if (recognitionRetryRef.current) clearTimeout(recognitionRetryRef.current);
    if (recognitionRef.current) {
      recognitionRef.current.onend = null;
      try {
        recognitionRef.current.stop();
      } catch {}
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current) {
      await audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }

    // Capture the last available pitch as the final plotted point when the session ends.
    if (latestPitchRef.current !== null && pitchSamplesRef.current.length === 0) {
      pitchSamplesRef.current.push(latestPitchRef.current);
      setPitchPoints([...pitchSamplesRef.current]);
    }

    const fullTranscript = [
      finalTranscriptRef.current,
      interimTranscriptRef.current,
    ]
      .filter(Boolean)
      .join(" ")
      .trim();

    const durationSeconds = Math.max(1, elapsedBeforePauseRef.current + (startedAtRef.current ? Math.floor((Date.now() - startedAtRef.current) / 1000) : 0));
    const wordCount = fullTranscript
      ? fullTranscript.split(/\s+/).filter(Boolean).length
      : 0;
    const wordsPerMinute = Math.round((wordCount / durationSeconds) * 60);
    const samples = pitchSamplesRef.current;
    const voicedSamples = samples.filter((value) => Number.isFinite(value));
    const meanPitch = voicedSamples.length
      ? Math.round(voicedSamples.reduce((total, value) => total + value, 0) / voicedSamples.length)
      : null;

    setTranscript(fullTranscript);
    setInterimTranscript("");
    setElapsed(durationSeconds);
    setAveragePitch(meanPitch);
    setSummary({
      transcript: fullTranscript,
      durationSeconds,
      wordsPerMinute,
      averagePitch: meanPitch,
      pauseCount: pauseCountRef.current,
      pitchSamples: samples.length,
    });
  }

  const displayedTranscript = [transcript, interimTranscript]
    .filter(Boolean)
    .join(" ");

  const chartWidth = Math.max(700, pitchPoints.length * 86 + 100);
  const pitchPolyline = pitchPoints.map((pitch, index) => {
    const x = 36 + index * 86;
    const boundedPitch = pitch == null ? null : Math.max(70, Math.min(350, pitch));
    const y = boundedPitch == null ? null : 190 - ((boundedPitch - 70) / (350 - 70)) * 160;
    return { x, y, pitch, time: (index + 1) * 2 };
  });
  const pitchSegments = [];
  let currentSegment = [];
  pitchPolyline.forEach((point) => {
    if (point.y == null) { if (currentSegment.length) pitchSegments.push(currentSegment); currentSegment = []; }
    else currentSegment.push(`${point.x},${point.y}`);
  });
  if (currentSegment.length) pitchSegments.push(currentSegment);

  return (
    <main className="quick-practice-page">
      <header className="practice-heading">
        <p className="practice-eyebrow">SPEAKKARO.AI</p>
        <h1>Quick Audio Practice</h1>
        <p>
          Practice speaking freely. Watch your transcript and voice pitch live.
          This session is temporary and is not saved to your account.
        </p>
      </header>

      {error && <div className="practice-error" role="alert">{error}</div>}

      <section className="practice-grid">
        <article className="practice-panel transcript-panel">
          <div className="practice-panel-heading">
            <div>
              <h2>Live transcript</h2>
              <p>Speech-to-text preview</p>
            </div>
            <span className="practice-live-tag">
              {status === "recording" ? "LIVE" : "TEXT"}
            </span>
          </div>

          <div className="practice-transcript">
            {displayedTranscript ? (
              <>
                {transcript}
                {interimTranscript && (
                  <span className="practice-interim">
                    {transcript ? " " : ""}{interimTranscript}
                  </span>
                )}
              </>
            ) : (
              <span className="practice-placeholder">
                Your words will appear here when you start speaking...
              </span>
            )}
          </div>

          {pauseMessage && status === "recording" && (
            <div className="practice-pause-message" role="status">
              {pauseMessage}
            </div>
          )}
        </article>

        <article className="practice-panel">
          <div className="practice-panel-heading">
            <div>
              <h2>Voice activity</h2>
              <p>Live microphone volume</p>
            </div>
          </div>

          <div className="practice-wave" aria-label="Live audio volume bars">
            {waveBars.map((height, index) => (
              <span
                key={index}
                style={{ height: `${Math.max(5, Math.min(100, height))}%` }}
              />
            ))}
          </div>

          <div className="practice-volume-caption">
            {status === "recording"
              ? "Listening to microphone"
              : "Start a session to view audio activity"}
          </div>
        </article>
      </section>

      <section className="practice-panel practice-pitch-panel">
        <div className="practice-panel-heading">
          <div>
            <h2>Pitch timeline</h2>
            <p>A new pitch sample is plotted every 2 seconds. Scroll to review the entire session.</p>
          </div>
          <div className="practice-pitch-value">
            <strong>{currentPitch ?? "--"}</strong>
            <span>Hz</span>
          </div>
        </div>

        <div className="practice-pitch-chart">
          <div className="practice-pitch-axis">
            <span>350 Hz</span>
            <span>210 Hz</span>
            <span>70 Hz</span>
          </div>
          <div className="practice-pitch-scroll">
          <svg
            viewBox={`0 0 ${chartWidth} 200`}
            style={{ width: `${chartWidth}px`, minWidth: `${chartWidth}px` }}
            role="img"
            aria-label="Pitch samples, one point every two seconds"
          >
            <line x1="0" y1="30" x2={chartWidth} y2="30" />
            <line x1="0" y1="110" x2={chartWidth} y2="110" />
            <line x1="0" y1="190" x2={chartWidth} y2="190" />
            {pitchSegments.map((segment, index) => <polyline key={index} points={segment.join(" ")} />)}
            {pitchPolyline.map((point, index) => (
              <g key={index}>
                <line x1={point.x} y1="25" x2={point.x} y2="190" className="pitch-sample-guide" />
                {point.y !== null ? <circle cx={point.x} cy={point.y} r="5" className="pitch-sample-dot" /> : <circle cx={point.x} cy="190" r="4" className="pitch-silence-dot" />}
                <text x={point.x} y="199" className="pitch-time-label">{formatTime(point.time)}</text>
              </g>
            ))}
          </svg>
          </div>
        </div>
        <div className="practice-chart-caption">
          {status === "recording"
            ? `Session timeline · ${pitchPoints.length} samples captured · one sample every 2 seconds`
            : status === "finished"
              ? `Complete session timeline · ${pitchPoints.length} samples captured`
              : "Start speaking to build your pitch timeline."}
        </div>
      </section>

      {summary && (
        <section className="practice-summary">
          <div className="practice-summary-heading">
            <div>
              <p className="practice-eyebrow">SESSION COMPLETE</p>
              <h2>Your quick practice summary</h2>
            </div>
            <button
              type="button"
              className="practice-secondary-button"
              onClick={() => {
                setSummary(null);
                setStatus("idle");
                setTranscript("");
                setInterimTranscript("");
                setElapsed(0);
                setPitchPoints([]);
                setCurrentPitch(null);
                setAveragePitch(null);
                setPauseCount(0);
                setPauseMessage("");
              }}
            >
              Clear session
            </button>
          </div>

          <div className="practice-summary-cards">
            <article>
              <span>Duration</span>
              <strong>{formatTime(summary.durationSeconds)}</strong>
            </article>
            <article>
              <span>Speaking pace</span>
              <strong>{summary.wordsPerMinute} WPM</strong>
            </article>
            <article>
              <span>Average estimated pitch</span>
              <strong>
                {summary.averagePitch == null
                  ? "Unavailable"
                  : `${summary.averagePitch} Hz`}
              </strong>
            </article>
            <article>
              <span>Detected pauses</span>
              <strong>{summary.pauseCount}</strong>
            </article>
          </div>

          <div className="practice-panel practice-summary-transcript">
            <h3>Final transcript</h3>
            <p>
              {summary.transcript ||
                "No transcript was recognised. Try speaking clearly and check microphone permission."}
            </p>
          </div>

          <p className="practice-privacy-note">
            This summary exists only in the current page session. It is not
            added to Progress or saved in browser storage.
          </p>
        </section>
      )}

      <footer className="practice-fixed-dock">
        <div className="practice-dock-timer"><span className={status === "recording" && !isPaused ? "dock-dot live" : "dock-dot"} />{formatTime(elapsed)}<small>{isPaused ? "PAUSED" : status === "recording" ? "RECORDING" : status === "finished" ? "COMPLETED" : "SESSION TIME"}</small></div>
        <div className="practice-dock-buttons">
          {status !== "recording" && status !== "finished" && <button className="practice-start-button" onClick={startPractice}>● Start Practice</button>}
          {status === "recording" && !isPaused && <button className="practice-pause-button" onClick={() => {
            pausedRef.current = true; setIsPaused(true); setStatus("paused");
            elapsedBeforePauseRef.current += Math.floor((Date.now() - startedAtRef.current) / 1000);
            startedAtRef.current = 0;
            if (animationRef.current) cancelAnimationFrame(animationRef.current);
            if (pitchIntervalRef.current) clearInterval(pitchIntervalRef.current);
            setPauseMessage("");
            if (recognitionRef.current) { recognitionRef.current.onend = null; try { recognitionRef.current.stop(); } catch {} }
          }}>Ⅱ Pause</button>}
          {status === "paused" && <button className="practice-start-button" onClick={() => {
            pausedRef.current = false; setIsPaused(false); setStatus("recording"); activeRef.current = true; startedAtRef.current = Date.now();
            if (recognitionRef.current) { recognitionRef.current.onend = () => { if (activeRef.current && !pausedRef.current) { try { recognitionRef.current.start(); } catch {} } }; try { recognitionRef.current.start(); } catch {} }
            const analyser = analyserRef.current; const ctx = audioContextRef.current;
            if (analyser && ctx) { const buffer = new Float32Array(analyser.fftSize); const update = () => { if (!activeRef.current || pausedRef.current || !analyserRef.current) return; analyser.getFloatTimeDomainData(buffer); const pitch = estimatePitch(buffer, ctx.sampleRate); latestPitchRef.current = pitch; setCurrentPitch(pitch); animationRef.current = requestAnimationFrame(update); }; animationRef.current = requestAnimationFrame(update); }
            pitchIntervalRef.current = setInterval(() => { const pitch = latestPitchRef.current; pitchSamplesRef.current.push(pitch); setPitchPoints((previous) => [...previous, pitch]); }, 2000);
          }}>▶ Resume</button>}
          {(status === "recording" || status === "paused") && <button className="practice-end-button" onClick={endPractice}>■ End Practice</button>}
          {status === "finished" && <button className="practice-start-button" onClick={startPractice}>● Start New Practice</button>}
        </div>
        <span className="practice-dock-hint">{isPaused ? "Take a breath. Resume when ready." : status === "recording" ? "Speak naturally. Pause whenever you need." : "Your practice is not saved."}</span>
      </footer>
    </main>
  );
}
