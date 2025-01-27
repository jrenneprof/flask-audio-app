print("Starting Flask app...")

from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory, flash
from werkzeug.utils import secure_filename
import os
from google.cloud import speech, texttospeech_v1

app = Flask(__name__)

# Configure upload and TTS folders
UPLOAD_FOLDER = 'uploads'
TTS_FOLDER = 'tts'
ALLOWED_EXTENSIONS = {'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TTS_FOLDER'] = TTS_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TTS_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files(folder):
    files = []
    for filename in os.listdir(folder):
        if allowed_file(filename):
            files.append(filename)
    files.sort(reverse=True)
    return files

@app.route('/')
def index():
    audio_files = get_files(app.config['UPLOAD_FOLDER'])
    tts_files = get_files(app.config['TTS_FOLDER'])
    return render_template('index.html', audio_files=audio_files, tts_files=tts_files)

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio_data' not in request.files:
        flash('No audio data')
        return redirect(request.url)
    file = request.files['audio_data']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Call Speech-to-Text API
        with open(file_path, 'rb') as audio_file:
            audio_data = audio_file.read()

        transcript = speech_to_text(audio_data)

        # Save transcript as a .txt file
        transcript_path = file_path + '.txt'
        with open(transcript_path, 'w') as f:
            f.write(transcript)

    return redirect('/')

@app.route('/upload_text', methods=['POST'])
def upload_text():
    text = request.form['text']
    if text:
        filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
        tts_path = os.path.join(app.config['TTS_FOLDER'], filename)

        # Call Text-to-Speech API
        audio_content = text_to_speech(text)

        # Save the generated audio file
        with open(tts_path, 'wb') as f:
            f.write(audio_content)

        # Save the input text for reference
        with open(tts_path + '.txt', 'w') as f:
            f.write(text)

    return redirect('/')

@app.route('/script.js', methods=['GET'])
def scripts_js():
    return send_file('./script.js')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/tts/<filename>')
def tts_file(filename):
    return send_from_directory(app.config['TTS_FOLDER'], filename)

# Google Speech-to-Text Function
def speech_to_text(audio_data):
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio_data)
    config = speech.RecognitionConfig(
        language_code="en-US",
        model="latest_long"
    )

    response = client.recognize(config=config, audio=audio)
    transcript = ''
    for result in response.results:
        transcript += result.alternatives[0].transcript + '\n'
    return transcript

# Google Text-to-Speech Function
def text_to_speech(text):
    try:
        # Debugging: Print the GOOGLE_APPLICATION_CREDENTIALS environment variable
        print("GOOGLE_APPLICATION_CREDENTIALS:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
        
        client = texttospeech_v1.TextToSpeechClient()
        input_data = texttospeech_v1.SynthesisInput(text=text)
        voice = texttospeech_v1.VoiceSelectionParams(
            language_code="en-US", 
            ssml_gender=texttospeech_v1.SsmlVoiceGender.NEUTRAL
        )
        audio_config = texttospeech_v1.AudioConfig(audio_encoding=texttospeech_v1.AudioEncoding.LINEAR16)

        response = client.synthesize_speech(
            input=input_data,
            voice=voice,
            audio_config=audio_config
        )
        return response.audio_content

    except Exception as e:
        # Print the error for debugging
        print("Error during Text-to-Speech API call:", e)
        raise

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
