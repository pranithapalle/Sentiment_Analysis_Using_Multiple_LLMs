import os
import json
import logging
from flask import Flask, request, jsonify, send_from_directory, render_template
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from google.cloud import texttospeech
from google.cloud import aiplatform

def setup_environment():
    """Set up environment variables and necessary directories."""
    load_dotenv()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(AUDIO_FOLDER, exist_ok=True)

def initialize_logging():
    """Initialize application logging."""
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)

UPLOAD_FOLDER = 'uploads'
AUDIO_FOLDER = 'static/audios'
setup_environment()

logger = initialize_logging()
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER

# Initialize Google Cloud Clients
tts_client = texttospeech.TextToSpeechClient()
aiplatform.init(project=os.getenv("GOOGLE_CLOUD_PROJECT"))



def synthesize_text_to_audio(text, output_path):
    """
    Convert text to speech and save as an audio file.
    Args:
        text (str): The text to be synthesized.
        output_path (str): The path to save the output audio.
    """
    try:
        logger.info(f"Synthesizing audio for text: {text}")
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        with open(output_path, 'wb') as file:
            file.write(response.audio_content)
        logger.info(f"Audio synthesized and saved to {output_path}")
    except Exception as e:
        logger.error(f"Error in text-to-speech synthesis: {e}")
        raise

def process_audio_with_llm(file_path):
    """
    Process an audio file using Vertex AI Multimodal LLM API for transcription and sentiment analysis.
    Args:
        file_path (str): Path to the audio file.
    Returns:
        tuple: Transcription text and sentiment analysis results.
    """
    try:
        logger.info(f"Processing audio file: {file_path}")
        with open(file_path, 'rb') as audio_file:
            audio_data = audio_file.read()

        endpoint = os.getenv("VERTEX_LLM_ENDPOINT")
        client = aiplatform.gapic.PredictionServiceClient(client_options={"api_endpoint": endpoint})

        instances = [{"content": audio_data, "mime_type": "audio/wav"}]
        parameters = {"tasks": ["transcription", "sentiment-analysis"]}

        response = client.predict(endpoint=endpoint, instances=instances, parameters=parameters)
        predictions = response.predictions[0]

        transcription = predictions.get("transcription", "")
        sentiment = predictions.get("sentiment", {})
        logger.info(f"Transcription: {transcription}, Sentiment: {sentiment}")

        return transcription, sentiment
    except Exception as e:
        logger.error(f"Error in processing audio with LLM API: {e}")
        return None, None


@app.route('/')
def index():
    """Serve the main application interface."""
    return render_template('index.html')

@app.route('/static/audios/<path:filename>')
def serve_audio_file(filename):
    """Serve the synthesized audio file."""
    return send_from_directory(AUDIO_FOLDER, filename)

@app.route('/api/record-transcribe', methods=['POST'])
def handle_record_transcription():
    """
    Handle audio file uploads, process transcription and sentiment analysis,
    and return synthesized audio of the results.
    """
    if 'audio' not in request.files or not request.files['audio'].filename:
        logger.warning("No audio file uploaded")
        return jsonify({'error': 'No audio file uploaded'}), 400

    file = request.files['audio']
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    logger.info(f"Audio file saved to {file_path}")

    # Process audio with LLM API
    transcription, sentiment = process_audio_with_llm(file_path)

    if not transcription or not sentiment:
        logger.error("Failed to process audio with LLM API")
        return jsonify({'error': 'Processing failed'}), 500

    # Prepare sentiment data
    sentiment_label = sentiment.get("label", "Neutral")
    sentiment_score = sentiment.get("score", 0)
    sentiment_magnitude = sentiment.get("magnitude", 0)

    combined_text = (f"The transcribed audio is: {transcription}. "
                     f"The sentiment of the speech is {sentiment_label} "
                     f"with a score of {sentiment_score} and magnitude of {sentiment_magnitude}.")

    # Synthesize audio from combined text
    synthesized_audio_path = os.path.join(AUDIO_FOLDER, f"response_{os.path.splitext(filename)[0]}.mp3")
    synthesize_text_to_audio(combined_text, synthesized_audio_path)

    logger.info(f"Response audio saved to {synthesized_audio_path}")
    return jsonify({
        'audioUrl': f"/static/audios/{os.path.basename(synthesized_audio_path)}",
        'transcription': transcription,
        'sentiment_label': sentiment_label,
        'sentiment_score': sentiment_score,
        'sentiment_magnitude': sentiment_magnitude
    })

if __name__ == '__main__':
    logger.info("Starting the Flask application...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
