import os
import json
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()
    samples = data.get("samples", [])
    corrections = data.get("corrections", [])

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    style_ctx = (
        "Study these writing samples from the author carefully — absorb their style, "
        "voice, rhythm, vocabulary, and sentence patterns:\n\n"
        + "\n\n---\n\n".join(
            f"Sample {i+1}:\n{s['text']}" for i, s in enumerate(samples)
        )
        if samples
        else "No style samples yet. Write in a clear literary fiction style."
    )

    corr_ctx = (
        "\n\nThe author has corrected past AI outputs. Learn from every entry — do not repeat these mistakes:\n\n"
        + "\n\n".join(
            f"Mistake {i+1}:\n  AI wrote: \"{c['original']}\"\n  Author's correction: \"{c['correction']}\""
            for i, c in enumerate(corrections)
        )
        if corrections
        else ""
    )

    system = (
        "You are a ghostwriter who writes entirely in the author's voice. "
        "Match their style precisely: sentence length, rhythm, vocabulary, tone, "
        "dialogue style, descriptive patterns — everything.\n\n"
        f"{style_ctx}{corr_ctx}\n\n"
        "Never explain. Never break character. Just write."
    )

    def stream_response():
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system,
        )
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield f"data: {json.dumps({'text': chunk.text})}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(stream_response()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

