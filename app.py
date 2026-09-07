import os
import base64
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from PIL import Image
import io

app = Flask(__name__)

# Configura Gemini con la API key da variabile d'ambiente
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

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
        # Leggi l'immagine
        img_bytes = file.read()
        img = Image.open(io.BytesIO(img_bytes))

        # Invia a Gemini Vision
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([
            "Sei un sistema di lettura contatori idrici. "
            "Analizza questa immagine e dimmi SOLO i numeri che vedi "
            "sul display del contatore dell'acqua, nell'ordine da sinistra "
            "a destra. Rispondi SOLO con i numeri, senza testo aggiuntivo, "
            "senza unità di misura, senza spazi. Solo le cifre.",
            img
        ])

        lettura = response.text.strip()
        return jsonify({'lettura': lettura})

    except Exception as e:
        return jsonify({'errore': f'Errore durante l\'analisi: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
