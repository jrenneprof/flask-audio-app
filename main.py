print("Starting Flask app...")

from datetime import datetime
from flask import Flask, render_template, request, send_file, send_from_directory, jsonify, flash, redirect
import os
from google.cloud import speech, texttospeech_v1, language_v1, storage

app = Flask(__name__)

# Google Cloud Storage Bucket Name
GCS_BUCKET_NAME = "classbucketassigment2"

# Configure folders (local for testing, Cloud Storage for production)
UPLOAD_FOLDER = 'uploads'
TTS_FOLDER = 'tts'
ALLOWED_EXTENSIONS = {'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TTS_FOLDER'] = TTS_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TTS_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Upload file to Google Cloud Storage
def upload_to_storage(bucket_name, source_file, destination_blob):
    """Uploads a file to GCS and returns the public URL"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob)
    blob.upload_from_filename(source_file)
    return f"https://storage.googleapis.com/{bucket_name}/{destination_blob}"

@app.route('/')
def index():
    audio_files = sorted(os.listdir(UPLOAD_FOLDER), reverse=True)
    tts_files = sorted(os.listdir(TTS_FOLDER), reverse=True)
    return render_template('index.html', audio_files=audio_files, tts_files=tts_files)

# Audio Upload Route (Speech-to-Text + Sentiment Analysis)
@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio_data' not in request.files:
        return jsonify({"error": "No audio data received"}), 400

    file = request.files['audio_data']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = datetime.now().strftime("%Y%m%d-%H%M%S") + '.wav'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Convert Speech to Text
        try:
            with open(file_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            transcript = speech_to_text(audio_data)
        except Exception as e:
            return jsonify({"error": f"Speech-to-text failed: {str(e)}"}), 500

        # Perform Sentiment Analysis
        sentiment_score, sentiment_magnitude = analyze_sentiment(transcript)

        # Determine Sentiment Label
        sentiment_label = "NEUTRAL"
        if sentiment_score > 0.25:
            sentiment_label = "POSITIVE"
        elif sentiment_score < -0.25:
            sentiment_label = "NEGATIVE"

        # Save Transcript & Sentiment Analysis
        transcript_path = file_path + '.txt'
        transcript_content = f"Transcription:\n{transcript}\nSentiment: {sentiment_label} (Score: {sentiment_score}, Magnitude: {sentiment_magnitude})"
        
        with open(transcript_path, 'w') as f:
            f.write(transcript_content)

        # Upload to Cloud Storage
        audio_url = upload_to_storage(GCS_BUCKET_NAME, file_path, f"uploads/{filename}")
        upload_to_storage(GCS_BUCKET_NAME, transcript_path, f"uploads/{filename}.txt")

        return jsonify({
            "transcript": transcript,
            "sentiment_label": sentiment_label,
            "sentiment_score": sentiment_score,
            "sentiment_magnitude": sentiment_magnitude,
            "audio_url": audio_url
        })

# Text-to-Speech (TTS) Route
@app.route('/upload_text', methods=['POST'])
def upload_text():
    text = request.form.get('text', '').strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    filename = datetime.now().strftime("%Y%m%d-%H%M%S") + '.wav'
    tts_path = os.path.join(app.config['TTS_FOLDER'], filename)

    # Convert Text to Speech
    try:
        audio_content = text_to_speech(text)
        with open(tts_path, 'wb') as f:
            f.write(audio_content)
    except Exception as e:
        return jsonify({"error": f"Text-to-Speech failed: {str(e)}"}), 500

    # Save Text Input for Reference
    with open(tts_path + '.txt', 'w') as f:
        f.write(text)

    # Upload to Cloud Storage
    tts_url = upload_to_storage(GCS_BUCKET_NAME, tts_path, f"tts/{filename}")
    upload_to_storage(GCS_BUCKET_NAME, tts_path + '.txt', f"tts/{filename}.txt")

    return jsonify({"tts_url": tts_url})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/tts/<filename>')
def tts_file(filename):
    return send_from_directory(app.config['TTS_FOLDER'], filename)

# Google Speech-to-Text Function
def speech_to_text(audio_data):
    """Convert speech to text using Google Speech-to-Text API"""
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio_data)
    config = speech.RecognitionConfig(
        language_code="en-US",
        model="default"
    )
    response = client.recognize(config=config, audio=audio)
    return " ".join(result.alternatives[0].transcript for result in response.results)

# Google Text-to-Speech Function
def text_to_speech(text):
    """Convert text to speech using Google Text-to-Speech API"""
    client = texttospeech_v1.TextToSpeechClient()
    input_data = texttospeech_v1.SynthesisInput(text=text)
    voice = texttospeech_v1.VoiceSelectionParams(
        language_code="en-US", 
        ssml_gender=texttospeech_v1.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech_v1.AudioConfig(audio_encoding=texttospeech_v1.AudioEncoding.LINEAR16)
    response = client.synthesize_speech(input=input_data, voice=voice, audio_config=audio_config)
    return response.audio_content

# Google Sentiment Analysis Function
def analyze_sentiment(text):
    """Analyze sentiment using Google Natural Language API"""
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
    response = client.analyze_sentiment(request={"document": document})
    sentiment = response.document_sentiment
    return sentiment.score, sentiment.magnitude

# Fix Missing `script.js` Route
@app.route('/script.js')
def scripts_js():
    return send_file(os.path.join(os.getcwd(), "script.js"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)



