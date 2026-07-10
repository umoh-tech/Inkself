import os
import json
from groq import Groq
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    filename = file.filename.lower()
    try:
        if filename.endswith(".txt") or filename.endswith(".md"):
            text = file.read().decode("utf-8", errors="ignore")
        elif filename.endswith(".docx"):
            import zipfile, xml.etree.ElementTree as ET, io
            file_bytes = file.read()
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                with z.open("word/document.xml") as doc_xml:
                    tree = ET.parse(doc_xml)
                    root = tree.getroot()
                    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                    paragraphs = root.findall(".//w:p", ns)
                    text = "\n".join("".join(t.text or "" for t in p.findall(".//w:t", ns)) for p in paragraphs).strip()
        else:
            return jsonify({"error": "Please upload .txt, .md, or .docx"}), 400
        if not text.strip():
            return jsonify({"error": "File appears to be empty"}), 400
        return jsonify({"text": text, "words": len(text.split())})
    except Exception as e:
        return jsonify({"error": f"Could not read file: {str(e)}"}), 500


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()
    samples = data.get("samples", [])
    corrections = data.get("corrections", [])

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    # Cap samples: max 3 samples, max 800 chars each to stay within token limits
    MAX_SAMPLES = 3
    MAX_SAMPLE_CHARS = 800
    trimmed_samples = samples[:MAX_SAMPLES]

    style_ctx = (
        "Study these writing samples from the author carefully — absorb their style, "
        "voice, rhythm, vocabulary, and sentence patterns:\n\n"
        + "\n\n---\n\n".join(
            f"Sample {i+1}:\n{s['text'][:MAX_SAMPLE_CHARS]}"
            for i, s in enumerate(trimmed_samples)
        )
        if trimmed_samples
        else "No style samples yet. Write in a clear literary fiction style."
    )

    # Cap corrections: max 5, max 300 chars each
    MAX_CORRECTIONS = 5
    MAX_CORR_CHARS = 300
    trimmed_corrections = corrections[:MAX_CORRECTIONS]

    corr_ctx = (
        "\n\nLearn from these past corrections — do not repeat these mistakes:\n\n"
        + "\n\n".join(
            f"Mistake {i+1}:\n  AI wrote: \"{c['original'][:150]}\"\n  Correction: \"{c['correction'][:MAX_CORR_CHARS]}\""
            for i, c in enumerate(trimmed_corrections)
        )
        if trimmed_corrections
        else ""
    )

    system = (
        "You are a ghostwriter who writes entirely in the author's voice. "
        "Match their style precisely: sentence length, rhythm, vocabulary, tone, "
        "dialogue style, descriptive patterns — everything.\n\n"
        f"{style_ctx}{corr_ctx}\n\nNever explain. Never break character. Just write."
    )

    def stream_response():
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield f"data: {json.dumps({'text': delta})}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(stream_response()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
