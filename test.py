import os
import speech_recognition as sr
import pyttsx3
from google import genai

print("🚀 Script is running...")

try:
    import speech_recognition as sr
    import pyttsx3
    from google import genai
    print("✅ Libraries imported successfully.")
except Exception as e:
    print(f"❌ Error importing libraries: {e}")

# Set up Gemini API
API_KEY = "AIzaSyBSMTfIUatKFMrj5onQmcxKvtH2f4ule5s"  # Replace with your actual API key
client = genai.Client(api_key=API_KEY)

# Initialize speech recognition
recognizer = sr.Recognizer()

# Initialize text-to-speech
engine = pyttsx3.init()
engine.setProperty('voice', engine.getProperty('voices')[0].id)  # Use the default voice

def listen():
    """Listen to user's voice and convert speech to text."""
    with sr.Microphone() as source:
        print("🎤 Speak now...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)  # Listen for up to 10 seconds
            text = recognizer.recognize_google(audio)  # Convert speech to text
            print(f"📝 You said: {text}")
            return text
        except sr.UnknownValueError:
            print("❌ Couldn't understand the audio.")
            return None
        except sr.RequestError:
            print("⚠ Speech Recognition API unavailable.")
            return None

def ask_gemini(query):
    """Send user query to Gemini API and get response."""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",  
            contents=query,
        )
        return response.text
    except Exception as e:
        print(f"🚨 Error with Gemini API: {e}")
        return "I couldn't get an answer."

def speak(text):
    """Convert text to speech and play it."""
    engine.say(text)
    engine.runAndWait()

# Main loop
while True:
    user_query = listen()  
    if user_query:
        response = ask_gemini(user_query)  
        print(f"🤖 AI: {response}")
        speak(response) 