from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
import pyttsx3
from google import genai
import tempfile
import os
import ffmpeg
import logging
import wave
import atexit

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Set up Gemini API
API_KEY = "AIzaSyBSMTfIUatKFMrj5onQmcxKvtH2f4ule5s"  # Replace with your actual API key
client = genai.Client(api_key=API_KEY)

def speak(text):
    """Convert text to speech and play it."""
    try:
        engine = pyttsx3.init()  # Create a new instance each time
        engine.setProperty('voice', engine.getProperty('voices')[0].id)
        engine.say(text)
        engine.runAndWait()  # Wait until speech is finished
        del engine  # Free up resources
    except Exception as e:
        print(f"🚨 Error in speak(): {e}")

def ask_gemini(query):
    """Send user query to Gemini API and get response."""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",  # Use the correct model name
            contents=query,
        )
        return response.text
    except Exception as e:
        print(f"🚨 Error with Gemini API: {e}")
        return "I couldn't get an answer."

@app.route("/")
def home():
    """Render the home page."""
    return render_template("index.html")

@app.route("/about")
def about():
    """Render the About page."""
    return render_template("about.html")

@app.route("/process", methods=["POST"])
def process():
    """Process text input and return Gemini's response."""
    try:
        data = request.get_json()
        if not data or "query" not in data:
            return jsonify({"error": "No query provided"}), 400

        user_input = data["query"]
        response = ask_gemini(user_input)
        speak(response)  # Speak the response
        return jsonify({"response": response})
    except Exception as e:
        print(f"🚨 Error in /process: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/process_audio", methods=["POST"])
def process_audio():
    """Process audio input and return Gemini's response."""
    try:
        if "audio" not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files["audio"]
        logging.debug(f"Received audio file: {audio_file.filename}")

        # Initialize the recognizer
        recognizer = sr.Recognizer()

        # Save the audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            audio_file.save(temp_audio.name)
            input_audio_path = temp_audio.name

        # Convert the audio to WAV format using ffmpeg
        output_audio_path = input_audio_path + ".wav"
        logging.debug(f"Converting {input_audio_path} to {output_audio_path}...")
        (
            ffmpeg
            .input(input_audio_path)
            .output(output_audio_path, acodec='pcm_s16le', ar='16000', ac=1)  # 16-bit, 16 kHz, mono
            .run(overwrite_output=True)
        )
        logging.debug(f"Conversion complete: {output_audio_path}")

        # Verify the converted WAV file
        if not os.path.exists(output_audio_path):
            return jsonify({"error": "Failed to convert audio file"}), 500

        # Check WAV file properties
        try:
            with wave.open(output_audio_path, 'rb') as wav_file:
                params = wav_file.getparams()
                logging.debug(f"WAV file properties: {params}")
                if params.nchannels != 1 or params.sampwidth != 2 or params.framerate != 16000:
                    logging.error("Invalid WAV file properties")
                    return jsonify({"error": "Invalid WAV file properties"}), 500
        except Exception as e:
            logging.error(f"🚨 Error reading WAV file: {e}")
            return jsonify({"error": "Invalid WAV file"}), 500

        # Process the converted WAV file
        logging.debug(f"Processing {output_audio_path}...")
        with sr.AudioFile(output_audio_path) as source:
            audio = recognizer.record(source)

        try:
            text = recognizer.recognize_google(audio)  # Convert speech to text
            logging.debug(f"📝 You said: {text}")
            response = ask_gemini(text)
            speak(response)  # Speak the response
            return jsonify({"response": response})
        except sr.UnknownValueError:
            logging.error("Couldn't understand the audio")
            return jsonify({"error": "Couldn't understand the audio"}), 400
        except sr.RequestError:
            logging.error("Speech Recognition API unavailable")
            return jsonify({"error": "Speech Recognition API unavailable"}), 500
    except Exception as e:
        logging.error(f"🚨 Error in /process_audio: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        # Clean up temporary files
        if os.path.exists(input_audio_path):
            os.remove(input_audio_path)
        if os.path.exists(output_audio_path):
            os.remove(output_audio_path)

if __name__ == "__main__":
    app.run(debug=True)
