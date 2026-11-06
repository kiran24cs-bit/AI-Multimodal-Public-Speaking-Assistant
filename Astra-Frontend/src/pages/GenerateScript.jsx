
import { useState } from "react";
import "./GenerateScript.css";

const API_URL = "http://127.0.0.1:8000";

export default function GenerateScript() {
  const [file, setFile] = useState(null);
  const [script, setScript] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleGenerate() {
    if (!file) {
      setError("Please upload a PDF or PPTX file first.");
      return;
    }

    setLoading(true);
    setError("");
    setScript("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${API_URL}/api/generate-script`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Script generation failed.");
      }

      setScript(data.script);
    } catch (err) {
      setError(
        err.message.includes("fetch")
          ? "Cannot connect to the backend. Start the Python server and try again."
          : err.message
      );
    } finally {
      setLoading(false);
    }
  }

  function downloadScript() {
    if (!script.trim()) return;

    const blob = new Blob([script], {
      type: "text/plain;charset=utf-8",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "presentation-script.txt";
    link.click();

    URL.revokeObjectURL(url);
  }

  return (
    <main className="script-page">
      <section className="script-header">
        <p className="script-eyebrow">SPEAKKARO.AI</p>
        <h1>Build your presentation script</h1>
        <p>
          Upload your slides, turn their content into a speaking
          script, and edit it before you practice.
        </p>
      </section>

      <section className="script-panel">
        <label htmlFor="presentation-file">
          Upload your presentation
        </label>

        <input
          id="presentation-file"
          type="file"
          accept=".pdf,.pptx,application/pdf,application/vnd.openxmlformats-officedocument.presentationml.presentation"
          onChange={(event) => {
            setFile(event.target.files?.[0] || null);
            setError("");
            setScript("");
          }}
        />

        <p className="script-hint">
          Supported formats: PDF and PPTX
        </p>

        {file && <p>Selected: {file.name}</p>}

        <button
          type="button"
          onClick={handleGenerate}
          disabled={loading || !file}
          className="script-primary-button"
        >
          {loading ? "Generating..." : "Generate script"}
        </button>

        {error && <p className="script-error">{error}</p>}
      </section>

      {script && (
        <section className="script-panel">
          <label htmlFor="generated-script">
            Edit your presentation script
          </label>

          <textarea
            id="generated-script"
            value={script}
            onChange={(event) => setScript(event.target.value)}
            rows={16}
          />

          <div className="script-actions">
            <button
              type="button"
              onClick={downloadScript}
              className="script-primary-button"
            >
              Download script
            </button>

            <button
              type="button"
              onClick={() => navigator.clipboard.writeText(script)}
              className="script-secondary-button"
            >
              Copy script
            </button>
          </div>
        </section>
      )}
    </main>
  );
}
