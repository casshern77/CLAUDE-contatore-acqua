import os
import io
import base64
import requests
from flask import Flask, request, jsonify, render_template
from PIL import Image

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analizza', methods=['POST'])
def analizza():
    # ... tutto il codice esistente ...

@app.route('/modelli')
def modelli():
    resp = requests.get(
        f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}",
        timeout=10
    )
    return resp.json()

# ← AGGIUNGI QUI IL NUOVO ENDPOINT
@app.route('/test-modello/<nome>')
def test_modello(nome):
    payload = {
        "contents": [{"parts": [{"text": "Rispondi solo con: OK"}]}]
    }
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{nome}:generateContent?key={GEMINI_API_KEY}",
        json=payload,
        timeout=15
    )
    return {"status": resp.status_code, "risposta": resp.json()}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
