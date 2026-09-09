import os
import io
import base64
import requests
from flask import Flask, request, jsonify, render_template
from PIL import Image

app = Flask(__name__)

GEMINI_KEYS = [
    os.environ.get("GEMINI_API_KEY_1"),
    os.environ.get("GEMINI_API_KEY_2"),
]

MODELLI = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
]

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analizza', methods=['POST'])
def analizza():
    if 'foto' not in request.files:
        return jsonify({'errore': 'Nessuna foto ricevuta.'}), 400

    file = request.files['foto']
    if file.filename == '':
        return jsonify({'errore': 'File non valido.'}), 400

    try:
        # Comprimi immagine
        img_bytes = file.read()
        img = Image.open(io.BytesIO(img_bytes))
        img.thumbnail((1024, 1024))
        buf = io.BytesIO()
        img.convert('RGB').save(buf, format='JPEG', quality=75)
        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        payload = {
            "contents": [{
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": img_b64
                        }
                    },
                    {
                        "text": (
                            "Sei un sistema di lettura contatori idrici. "
                            "Analizza questa immagine e dimmi SOLO i numeri che vedi "
                            "sul display del contatore dell'acqua, nell'ordine da sinistra "
                            "a destra. Rispondi SOLO con i numeri, senza testo aggiuntivo, "
                            "senza unità di misura, senza spazi. Solo le cifre."
                        )
                    }
                ]
            }]
        }

        tentativi_eseguiti = []

        for key_idx, api_key in enumerate(GEMINI_KEYS, start=1):
            if not api_key:
                continue
            for modello in MODELLI:
                label = f"account_{key_idx} / {modello}"
                tentativi_eseguiti.append(label)
                try:
                    url = f"{BASE_URL}/{modello}:generateContent?key={api_key}"
                    resp = requests.post(url, json=payload, timeout=10)

                    if resp.status_code == 200:
                        data = resp.json()
                        lettura = data['candidates'][0]['content']['parts'][0]['text'].strip()
                        return jsonify({
                            'lettura': lettura,
                            'tentativo_riuscito': label,
                            'tentativi': tentativi_eseguiti
                        })
                    # Qualsiasi errore → prossimo tentativo
                    else:
                        continue

                except requests.exceptions.Timeout:
                    continue
                except Exception:
                    continue

        return jsonify({
            'errore': 'Tutti i server sono temporaneamente occupati. Riprova tra qualche secondo.',
            'tentativi': tentativi_eseguiti
        }), 503

    except Exception as e:
        return jsonify({'errore': f'Errore elaborazione immagine: {str(e)}'}), 500

@app.route('/modelli')
def modelli():
    api_key = GEMINI_KEYS[0]
    resp = requests.get(
        f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
        timeout=10
    )
    return resp.json()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
