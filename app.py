import os
import io
import base64
import requests
from flask import Flask, request, jsonify, render_template
from PIL import Image

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

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
        # Leggi e comprimi l'immagine per ridurre i tempi di upload verso Gemini
        img_bytes = file.read()
        img = Image.open(io.BytesIO(img_bytes))
        
        # Ridimensiona se troppo grande (max 1024px lato lungo)
        img.thumbnail((1024, 1024))
        
        # Converti in JPEG compresso
        buf = io.BytesIO()
        img.convert('RGB').save(buf, format='JPEG', quality=75)
        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        # Chiamata diretta alle API REST di Gemini (più veloce della libreria)
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

        resp = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=payload,
            timeout=90
        )
        resp.raise_for_status()
        data = resp.json()

        lettura = data['candidates'][0]['content']['parts'][0]['text'].strip()
        return jsonify({'lettura': lettura})

    except requests.exceptions.Timeout:
        return jsonify({'errore': 'Timeout: Gemini ha impiegato troppo. Riprova.'}), 504
    except Exception as e:
        return jsonify({'errore': f'Errore: {str(e)}'}), 500





@app.route('/modelli')
def modelli():
    resp = requests.get(
        f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}",
        timeout=10
    )
    return resp.json()
    





if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
