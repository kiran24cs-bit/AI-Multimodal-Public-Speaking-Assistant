import os
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pptx import Presentation
from pptx.exc import PackageNotFoundError

from PPTanalyzer import analyze_pptx

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024  # 30 MB
# CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})
CORS(app)
OUTPUT_DIR = Path(__file__).parent / "output" / "ppt_analysed"


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "message": "PPTX analyzer API is running"})


@app.post("/api/analyze-ppt")
def analyze_ppt():
    if "file" not in request.files:
        return jsonify({"error": "No file was uploaded. Choose a .pptx file first."}), 400
    uploaded = request.files["file"]
    filename = secure_filename(uploaded.filename or "")
    if not filename:
        return jsonify({"error": "The uploaded file has no valid filename."}), 400
    if Path(filename).suffix.lower() != ".pptx":
        return jsonify({"error": "Only PowerPoint .pptx files are supported."}), 400

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(prefix="speakaro_", suffix=".pptx", delete=False) as temp:
            uploaded.save(temp)
            temp_path = Path(temp.name)
        # Validate that the uploaded file is a readable PowerPoint package.
        Presentation(str(temp_path))
        report = analyze_pptx(temp_path, OUTPUT_DIR)
        report["file_name"] = filename
        return jsonify({"success": True, "report": report})
    except (PackageNotFoundError, ValueError, KeyError) as exc:
        return jsonify({"error": f"Could not analyze this PowerPoint file: {exc}"}), 400
    except Exception:
        app.logger.exception("PPTX analysis failed")
        return jsonify({"error": "Analysis failed unexpectedly. Check the Flask terminal for details."}), 500
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({"error": "File is too large. Maximum upload size is 30 MB."}), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
