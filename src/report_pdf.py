"""
Pure Python PDF generator for Astra-Hunters Speech Analysis Reports.
Generates a clean, valid PDF 1.4 document without external dependencies.
"""
from typing import Dict, Any


def escape_pdf_text(text: str) -> str:
    """Escape special characters in PDF strings."""
    if not text:
        return ""
    # Remove unsupported characters outside latin1/ascii for Type1 standard fonts
    clean = ""
    for char in str(text):
        if ord(char) < 128:
            clean += char
        elif char in "“”":
            clean += '"'
        elif char in "‘’":
            clean += "'"
        elif char in "—–":
            clean += "-"
        elif char in "•":
            clean += "*"
        else:
            clean += " "
    return clean.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def wrap_text(text: str, max_chars: int = 80) -> list[str]:
    """Wraps text into lines not exceeding max_chars."""
    lines = []
    paragraphs = str(text).split("\n")
    for para in paragraphs:
        para = para.strip()
        if not para:
            lines.append("")
            continue
        words = para.split(" ")
        current_line = []
        current_len = 0
        for word in words:
            if not word:
                continue
            if current_len + len(word) + (1 if current_line else 0) <= max_chars:
                current_line.append(word)
                current_len += len(word) + (1 if current_line else 0)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_len = len(word)
        if current_line:
            lines.append(" ".join(current_line))
    return lines


def create_speech_report_pdf(speech: Dict[str, Any]) -> bytes:
    """
    Creates a formatted Astra-Hunters-2.0 Speech Report PDF.
    Returns bytes of the PDF file.
    """
    title = speech.get("title") or "Speech Analysis Report"
    date_str = speech.get("date") or "N/A"
    score = speech.get("score")
    score_display = f"{score}/100" if score is not None else "N/A"
    
    delivery = speech.get("deliveryScore") or speech.get("delivery")
    vocal = speech.get("vocalScore") or speech.get("vocal")
    body_lang = speech.get("bodyLanguageScore") or speech.get("body_language")
    accent = speech.get("detectedAccent") or "Standard English"
    
    pace = speech.get("pace")
    pace_str = f"{pace} WPM" if pace is not None else "N/A"
    
    fillers = speech.get("fillerCount") or speech.get("fillerWordsCount")
    fillers_str = str(fillers) if fillers is not None else "0"
    
    pauses = speech.get("pauseCount")
    pauses_str = str(pauses) if pauses is not None else "0"
    
    duration = speech.get("duration")
    if isinstance(duration, (int, float)):
        mins = int(duration) // 60
        secs = int(duration) % 60
        duration_str = f"{mins}m {secs:02d}s"
    elif duration:
        duration_str = str(duration)
    else:
        duration_str = "N/A"
        
    feedback = speech.get("feedback") or speech.get("coachingReport") or "Speech was successfully recorded and analyzed."
    transcript = speech.get("transcript") or speech.get("transcription") or "No transcription recorded for this session."
    drawbacks = speech.get("drawbacks") or []

    # PDF Stream Builder (Points: 595.28 x 841.89 = A4 portrait)
    # Origin (0,0) is bottom-left, Top is y=841.89
    stream_cmds = []

    # 1. Header Background Banner
    stream_cmds.append("0.05 0.08 0.14 rg")  # Dark navy #0d1524
    stream_cmds.append("0 750 595.28 92 re f")

    # Accent green stripe
    stream_cmds.append("0.41 0.90 0.58 rg")  # Green #68e694
    stream_cmds.append("0 746 595.28 4 re f")

    # Brand Title
    stream_cmds.append("BT /F1 18 Tf 1 1 1 rg 40 795 Td (ASTRA-HUNTERS 2.0) Tj ET")
    stream_cmds.append("BT /F2 10 Tf 0.6 0.7 0.8 rg 40 775 Td (MULTIMODAL AI PUBLIC SPEAKING EVALUATION REPORT) Tj ET")
    stream_cmds.append(f"BT /F2 10 Tf 0.8 0.8 0.8 rg 420 775 Td (Date: {escape_pdf_text(date_str)}) Tj ET")

    # 2. Speech Title Card
    stream_cmds.append("0.96 0.97 0.98 rg")  # Light gray background
    stream_cmds.append("40 670 515.28 55 re f")
    stream_cmds.append("0.85 0.88 0.91 RG 1 w")  # Border
    stream_cmds.append("40 670 515.28 55 re s")

    stream_cmds.append(f"BT /F1 15 Tf 0.1 0.15 0.2 rg 55 700 Td ({escape_pdf_text(title[:60])}) Tj ET")
    stream_cmds.append(f"BT /F2 10 Tf 0.4 0.45 0.5 rg 55 682 Td (Session Recording Report - Accent: {escape_pdf_text(accent)}) Tj ET")

    # Overall Score Box
    stream_cmds.append("0.09 0.24 0.15 rg")  # Dark green box
    stream_cmds.append("460 675 80 45 re f")
    stream_cmds.append("0.41 0.90 0.58 rg")
    stream_cmds.append(f"BT /F1 16 Tf 475 695 Td ({escape_pdf_text(score_display)}) Tj ET")
    stream_cmds.append("BT /F2 8 Tf 1 1 1 rg 480 682 Td (Score) Tj ET")

    # 3. Performance Metrics Grid (Row 1)
    y_m = 615
    metrics = [
        ("Pace", pace_str),
        ("Filler Words", fillers_str),
        ("Pauses", pauses_str),
        ("Duration", duration_str),
    ]
    card_w = 120
    for idx, (label, val) in enumerate(metrics):
        x = 40 + idx * 131
        stream_cmds.append("0.95 0.96 0.98 rg")
        stream_cmds.append(f"{x} {y_m} {card_w} 40 re f")
        stream_cmds.append("0.85 0.88 0.91 RG 0.5 w")
        stream_cmds.append(f"{x} {y_m} {card_w} 40 re s")
        stream_cmds.append(f"BT /F2 8 Tf 0.4 0.45 0.5 rg {x+10} {y_m+26} Td ({escape_pdf_text(label.upper())}) Tj ET")
        stream_cmds.append(f"BT /F1 12 Tf 0.1 0.15 0.25 rg {x+10} {y_m+10} Td ({escape_pdf_text(str(val))}) Tj ET")

    # Performance Metrics Grid (Row 2 - Multimodal Scores)
    y_m2 = 565
    multi_metrics = [
        ("Delivery Score", f"{delivery}/100" if delivery is not None else "N/A"),
        ("Vocal Expression", f"{vocal}/100" if vocal is not None else "N/A"),
        ("Body Language", f"{body_lang}/100" if body_lang is not None else "N/A"),
        ("Detected Accent", str(accent)),
    ]
    for idx, (label, val) in enumerate(multi_metrics):
        x = 40 + idx * 131
        stream_cmds.append("0.95 0.96 0.98 rg")
        stream_cmds.append(f"{x} {y_m2} {card_w} 40 re f")
        stream_cmds.append("0.85 0.88 0.91 RG 0.5 w")
        stream_cmds.append(f"{x} {y_m2} {card_w} 40 re s")
        stream_cmds.append(f"BT /F2 8 Tf 0.4 0.45 0.5 rg {x+10} {y_m2+26} Td ({escape_pdf_text(label.upper())}) Tj ET")
        stream_cmds.append(f"BT /F1 11 Tf 0.1 0.15 0.25 rg {x+10} {y_m2+10} Td ({escape_pdf_text(str(val))}) Tj ET")

    # 4. AI Coaching Feedback
    y_cursor = 530
    stream_cmds.append(f"BT /F1 12 Tf 0.1 0.15 0.25 rg 40 {y_cursor} Td (AI COACHING RECOMMENDATIONS) Tj ET")
    y_cursor -= 6
    stream_cmds.append(f"0.41 0.90 0.58 RG 2 w 40 {y_cursor} m 220 {y_cursor} l S")
    y_cursor -= 18

    feedback_lines = wrap_text(feedback, max_chars=82)[:10]
    for line in feedback_lines:
        if y_cursor < 200:
            break
        stream_cmds.append(f"BT /F2 9.5 Tf 0.2 0.25 0.3 rg 40 {y_cursor} Td ({escape_pdf_text(line)}) Tj ET")
        y_cursor -= 14

    # 5. Areas to Improve / Drawbacks (if any)
    if drawbacks and isinstance(drawbacks, list):
        y_cursor -= 10
        stream_cmds.append(f"BT /F1 11 Tf 0.1 0.15 0.25 rg 40 {y_cursor} Td (AREAS FOR IMPROVEMENT) Tj ET")
        y_cursor -= 16
        for drawback in drawbacks[:4]:
            if y_cursor < 160:
                break
            stream_cmds.append(f"BT /F2 9 Tf 0.2 0.25 0.3 rg 50 {y_cursor} Td (* {escape_pdf_text(str(drawback)[:80])}) Tj ET")
            y_cursor -= 13

    # 6. Speech Transcription Excerpt
    y_cursor -= 12
    if y_cursor > 140:
        stream_cmds.append(f"BT /F1 11 Tf 0.1 0.15 0.25 rg 40 {y_cursor} Td (SPEECH TRANSCRIPTION EXCERPT) Tj ET")
        y_cursor -= 16
        trans_lines = wrap_text(transcript, max_chars=85)[:6]
        for tline in trans_lines:
            if y_cursor < 70:
                break
            stream_cmds.append(f"BT /F3 8.5 Tf 0.35 0.4 0.45 rg 40 {y_cursor} Td ({escape_pdf_text(tline)}) Tj ET")
            y_cursor -= 12

    # 7. Footer
    stream_cmds.append("0.85 0.88 0.91 RG 1 w 40 45 m 555 45 l S")
    stream_cmds.append("BT /F2 8 Tf 0.5 0.55 0.6 rg 40 32 Td (Astra-Hunters-2.0 Multimodal Evaluation Engine - Evaluated with Whisper, Wav2Vec2 & Groq AI) Tj ET")
    stream_cmds.append("BT /F2 8 Tf 0.5 0.55 0.6 rg 475 32 Td (Page 1 of 1) Tj ET")

    # Combine content stream
    content = "\n".join(stream_cmds).encode("latin-1", errors="replace")

    # Assemble PDF Objects
    objects = []
    
    # Obj 1: Catalog
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    # Obj 2: Pages
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    # Obj 3: Page
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] "
        b"/Resources << /Font << /F1 4 0 R /F2 5 0 R /F3 6 0 R >> >> "
        b"/Contents 7 0 R >>"
    )
    # Obj 4: Font F1 Bold
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    # Obj 5: Font F2 Regular
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    # Obj 6: Font F3 Oblique
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique >>")
    # Obj 7: Contents
    objects.append(f"<< /Length {len(content)} >>\nstream\n".encode("ascii") + content + b"\nendstream")

    # Build PDF with xref table
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]

    for i, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{i} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")

    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )

    return bytes(output)
