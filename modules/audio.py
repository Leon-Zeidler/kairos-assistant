from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_audio_briefing(text_content):
    """Verwandelt Text in eine MP3-Datei via OpenAI API"""
    if not client: return None
    
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx", # Stimmen: alloy, echo, fable, onyx, nova, shimmer
            input=text_content
        )
        
        # Speichern als temporäre Datei
        path = "daily_briefing.mp3"
        response.stream_to_file(path)
        return path
    except Exception as e:
        print(f"Audio Error: {e}")
        return None

def transcribe_audio(audio_file_path):
    """Verwandelt Sprache in Text mit Whisper"""
    if not client: return None
    
    try:
        # Datei zum Lesen öffnen
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                language="en" # Oder "de" wenn du deutsch sprichst
            )
        return transcript.text
    except Exception as e:
        print(f"Whisper Error: {e}")
        return None