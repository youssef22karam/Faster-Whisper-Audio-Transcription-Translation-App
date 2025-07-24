# audio_transcription_app.py
import os
import time
import socket
from flask import Flask, render_template_string, request, jsonify
from faster_whisper import WhisperModel
import ssl
from tempfile import NamedTemporaryFile
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta, timezone
import multiprocessing
import requests
import json

# ===== CONFIGURABLE LANGUAGE SETTINGS =====
# Whisper transcription language (ISO 639-1 codes)
# Common options: 'en' (English), 'es' (Spanish), 'fr' (French), 'de' (German), 
# 'it' (Italian), 'pt' (Portuguese), 'ru' (Russian), 'ja' (Japanese), 'ko' (Korean),
# 'zh' (Chinese), 'ar' (Arabic), 'hi' (Hindi), 'nl' (Dutch), 'sv' (Swedish), etc.
WHISPER_LANGUAGE = "es"  # Change this to your desired transcription language

# Translation source language (what language Whisper transcribed)
TRANSLATION_SOURCE_LANG = "es"  # Should match WHISPER_LANGUAGE

# Translation target languages
TRANSLATION_TARGET_1 = "en"     # First translation language (English)
TRANSLATION_TARGET_2 = "ar"     # Second translation language (Arabic)

# Language display names for the UI
TRANSLATION_TARGET_1_NAME = "English Translation"
TRANSLATION_TARGET_2_NAME = "Arabic Translation"

# Default text for translation boxes
TRANSLATION_TARGET_1_DEFAULT = "Translation will appear here..."
TRANSLATION_TARGET_2_DEFAULT = "الترجمة ستظهر هنا..."

# Whisper model settings
MODEL_SIZE = "medium"  # Options: tiny, base, small, medium, large, large-v2, large-v3
DEVICE = "cpu"         # Options: cpu, cuda
COMPUTE_TYPE = "int8"  # Options: int8, float16, float32
# ==========================================

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE, cpu_threads=multiprocessing.cpu_count())

# Simple translation function using Google Translate API
def translate_text_simple(text, source_lang=TRANSLATION_SOURCE_LANG, target_lang='en'):
    """Simple translation using Google Translate via web scraping approach"""
    try:
        # Using a simple approach with requests
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': source_lang,
            'tl': target_lang,
            'dt': 't',
            'q': text
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result and len(result) > 0 and result[0]:
                translated_text = ''.join([item[0] for item in result[0] if item[0]])
                return translated_text
        
        return None
    except Exception as e:
        print(f"Translation error for {target_lang}: {e}")
        return None

print("Translation system initialized successfully")

HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Audio Transcription</title>
  <style>
    :root {{
      --primary: #4f46e5;
      --danger: #ef4444;
      --accent: #a78bfa;
      --light: #f9fafb;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background-color: var(--light);
      margin: 0;
      padding: 0;
      height: 100dvh;
      display: flex;
      justify-content: center;
      align-items: stretch;
    }}

    .container {{
      display: flex;
      flex-direction: column;
      width: 100%;
      max-width: 420px;
      background: white;
      height: 100%;
      box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }}

    h1 {{
      text-align: center;
      color: var(--primary);
      font-size: 1.5rem;
      margin: 12px 0;
    }}

    .section {{
      flex: 1;
      overflow-y: auto;
      padding: 12px;
    }}

    .btn {{
      width: 100%;
      padding: 14px;
      font-size: 16px;
      border: none;
      border-radius: 12px;
      margin: 8px 0;
      cursor: pointer;
    }}

    .record-btn {{
      background: var(--primary);
      color: white;
    }}

    .record-btn.recording {{
      background: var(--danger);
    }}

    .secondary-btn {{
      background: #e0e7ff;
      color: var(--primary);
    }}

    textarea, .translation-box {{
      width: 100%;
      padding: 12px;
      font-size: 15px;
      border-radius: 10px;
      border: 1px solid #e5e7eb;
      resize: none;
      margin-top: 8px;
      min-height: 80px;
    }}

    .translation-box {{
      background-color: #f3f4f6;
    }}

    .translation-label {{
      font-weight: 600;
      color: var(--primary);
      margin-top: 12px;
      margin-bottom: 4px;
    }}

    audio {{
      width: 100%;
      margin-top: 10px;
    }}

    .status {{
      text-align: center;
      font-weight: 500;
      color: var(--accent);
      margin: 10px 0;
    }}

    .bottom-bar {{
      padding: 12px;
      background: white;
      border-top: 1px solid #ddd;
    }}

    .hidden {{
      display: none;
    }}

    @media (max-height: 700px) {{
      .btn, textarea {{
        font-size: 14px;
        padding: 10px;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Audio Transcription</h1>

    <div class="section">
      <p id="status" class="status">Tap to record</p>
      <audio id="audioPlayback" controls class="hidden"></audio>

      <textarea id="transcriptionText" placeholder="Transcription will appear here..."></textarea>
      
      <div class="translation-label">{TRANSLATION_TARGET_1_NAME}:</div>
      <div id="translation1" class="translation-box">{TRANSLATION_TARGET_1_DEFAULT}</div>
      
      <div class="translation-label">{TRANSLATION_TARGET_2_NAME}:</div>
      <div id="translation2" class="translation-box">{TRANSLATION_TARGET_2_DEFAULT}</div>
    </div>

    <div class="bottom-bar">
      <button id="newRecordingButton" class="btn secondary-btn">New Recording</button>
      <button id="recordButton" class="btn record-btn">Start Recording</button>
    </div>
  </div>

  <script>
    const recordButton = document.getElementById('recordButton');
    const statusText = document.getElementById('status');
    const audioPlayback = document.getElementById('audioPlayback');
    const transcriptionText = document.getElementById('transcriptionText');
    const translation1 = document.getElementById('translation1');
    const translation2 = document.getElementById('translation2');
    const newRecordingButton = document.getElementById('newRecordingButton');

    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

    recordButton.addEventListener('click', toggleRecording);

    function playStartBeep() {{
      const ctx = new AudioContext();
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();

      osc1.frequency.value = 800;
      osc2.frequency.value = 1000;

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(ctx.destination);

      osc1.start();
      osc1.stop(ctx.currentTime + 0.2);

      osc2.start(ctx.currentTime + 0.2);
      osc2.stop(ctx.currentTime + 0.4);
    }}

    function playStopBeep() {{
      const ctx = new AudioContext();
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();

      osc1.frequency.value = 1000;
      osc2.frequency.value = 600;

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(ctx.destination);

      osc1.start();
      osc1.stop(ctx.currentTime + 0.2);

      osc2.start(ctx.currentTime + 0.2);
      osc2.stop(ctx.currentTime + 0.4);
    }}

    function toggleRecording() {{
      if (!isRecording) {{
        playStartBeep(); // Ascending beep on start

        navigator.mediaDevices.getUserMedia({{ audio: true }}).then(stream => {{
          mediaRecorder = new MediaRecorder(stream);
          audioChunks = [];

          mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

          mediaRecorder.onstop = () => {{
            const audioBlob = new Blob(audioChunks, {{ type: 'audio/wav' }});
            const audioUrl = URL.createObjectURL(audioBlob);
            audioPlayback.src = audioUrl;
            audioPlayback.classList.remove('hidden');
            stream.getTracks().forEach(track => track.stop());
            sendAudioToServer(audioBlob);
          }};

          mediaRecorder.start();
          isRecording = true;
          recordButton.textContent = 'Stop Recording';
          recordButton.classList.add('recording');
          statusText.textContent = 'Recording...';
        }}).catch(err => {{
          console.error('Microphone error:', err);
          statusText.textContent = 'Microphone not available';
        }});
      }} else {{
        mediaRecorder.stop();
        playStopBeep(); // Descending beep on stop

        isRecording = false;
        recordButton.textContent = 'Start Recording';
        recordButton.classList.remove('recording');
        statusText.textContent = 'Processing...';
      }}
    }}

    function sendAudioToServer(blob) {{
      const formData = new FormData();
      formData.append('audio', blob, 'recording.wav');

      fetch('/upload', {{
        method: 'POST',
        body: formData
      }})
      .then(res => res.json())
      .then(data => {{
        console.log('Upload response:', data);
        if (data.transcription) {{
          transcriptionText.value = data.transcription;
          statusText.textContent = 'Translating...';
          translateText(data.transcription);
        }} else {{
          statusText.textContent = 'Transcription failed: ' + (data.error || 'Unknown error');
        }}
      }})
      .catch(err => {{
        console.error('Upload error:', err);
        statusText.textContent = 'Upload error: ' + err.message;
      }});
    }}

    function translateText(text) {{
      console.log('Translating text:', text);
      
      fetch('/translate', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ text: text }})
      }})
      .then(res => res.json())
      .then(data => {{
        console.log('Translation response:', data);
        if (data.error) {{
          statusText.textContent = 'Translation error: ' + data.error;
          translation1.textContent = 'Translation failed';
          translation2.textContent = 'Translation failed';
        }} else {{
          translation1.textContent = data.translation1 || 'No translation available';
          translation2.textContent = data.translation2 || 'No translation available';
          statusText.textContent = 'Done';
        }}
      }})
      .catch(err => {{
        console.error('Translation error:', err);
        statusText.textContent = 'Translation error: ' + err.message;
        translation1.textContent = 'Translation failed';
        translation2.textContent = 'Translation failed';
      }});
    }}

    transcriptionText.addEventListener('input', function() {{
      const text = transcriptionText.value.trim();
      if (text.length > 1) {{
        statusText.textContent = 'Translating...';
        translateText(text);
      }}
    }});

    newRecordingButton.addEventListener('click', function() {{
      transcriptionText.value = '';
      translation1.textContent = '{TRANSLATION_TARGET_1_DEFAULT}';
      translation2.textContent = '{TRANSLATION_TARGET_2_DEFAULT}';
      audioPlayback.classList.add('hidden');
      statusText.textContent = 'Tap to record';
    }});
  </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file received'}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = f"recording_{int(time.time())}.wav"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    try:
        audio_file.save(filepath)
        print(f"Saved audio file: {filepath}")
        
        segments, _ = model.transcribe(filepath, language=WHISPER_LANGUAGE, beam_size=2, word_timestamps=False, vad_filter=False)
        transcription = " ".join(segment.text for segment in segments)
        
        print(f"Transcription: {transcription}")
        return jsonify({'transcription': transcription})
        
    except Exception as e:
        print(f"Transcription error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

@app.route('/translate', methods=['POST'])
def translate_text():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
            
        text = data.get('text', '')
        if not text or not text.strip():
            return jsonify({'error': 'No text provided or text is empty'}), 400

        print(f"Translating text: '{text}'")
        
        # Translate to first target language
        translation1_text = translate_text_simple(text, TRANSLATION_SOURCE_LANG, TRANSLATION_TARGET_1)
        if not translation1_text:
            translation1_text = "Translation failed"
        
        # Translate to second target language
        translation2_text = translate_text_simple(text, TRANSLATION_SOURCE_LANG, TRANSLATION_TARGET_2)
        if not translation2_text:
            translation2_text = "Translation failed"
        
        print(f"Translation 1 ({TRANSLATION_TARGET_1}): {translation1_text}")
        print(f"Translation 2 ({TRANSLATION_TARGET_2}): {translation2_text}")
        
        return jsonify({
            'translation1': translation1_text,
            'translation2': translation2_text
        })
                
    except Exception as e:
        print(f"Translation error: {e}")
        return jsonify({'error': f'Translation failed: {str(e)}'}), 500

def generate_self_signed_cert():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
    subject = issuer = x509.Name([
        x509.NameAttribute(x509.NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(x509.NameOID.STATE_OR_PROVINCE_NAME, "CA"),
        x509.NameAttribute(x509.NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(x509.NameOID.ORGANIZATION_NAME, "My Company"),
        x509.NameAttribute(x509.NameOID.COMMON_NAME, "localhost"),
    ])
    cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(
        private_key.public_key()
    ).serial_number(x509.random_serial_number()).not_valid_before(
        datetime.now(timezone.utc)
    ).not_valid_after(
        datetime.now(timezone.utc) + timedelta(days=1)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False,
    ).sign(private_key, hashes.SHA256(), default_backend())

    cert_file = NamedTemporaryFile(delete=False)
    key_file = NamedTemporaryFile(delete=False)
    cert_file.write(cert.public_bytes(serialization.Encoding.PEM))
    key_file.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))
    cert_file.close()
    key_file.close()
    return cert_file.name, key_file.name

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception:
        return "127.0.0.1"

if __name__ == '__main__':
    try:
        cert_file, key_file = generate_self_signed_cert()
        context = (cert_file, key_file)
        local_ip = get_local_ip()
        port = 5000
        print(f"\nGo to: https://{local_ip}:{port} (ignore browser warnings)")
        app.run(host='0.0.0.0', port=port, ssl_context=context, debug=True)
    finally:
        if 'cert_file' in locals() and os.path.exists(cert_file): 
            os.unlink(cert_file)
        if 'key_file' in locals() and os.path.exists(key_file): 
            os.unlink(key_file)