import streamlit as st
import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv
from modules import auth, storage, mail_agent, brain, ui, audio # <--- Audio importieren

st.set_page_config(page_title="AI Chat", page_icon="💬", layout="wide")

# --- SIDEBAR ---
ui.render_sidebar("Chat")

load_dotenv()

# --- SETUP ---
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None
creds = auth.get_creds()
service = auth.get_service()

# --- DATEN LADEN (HISTORY) ---
if 'full_chat_history' not in st.session_state:
    st.session_state.full_chat_history = storage.load_from_drive(creds, 'chat_history', [])

# --- CONTEXT ---
@st.cache_data(ttl=300)
def get_system_context():
    context_text = f"Current Date: {datetime.datetime.now().strftime('%A, %B %d, %Y')}.\n\n"
    
    # 1. CALENDAR
    now = datetime.datetime.now()
    t_min = now.isoformat() + 'Z'
    t_max = (now + datetime.timedelta(days=3)).isoformat() + 'Z'
    events = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True, orderBy='startTime').execute().get('items', [])
    
    context_text += "📅 CALENDAR (Next 3 days):\n"
    if not events: context_text += "- No events.\n"
    for e in events:
        start = e['start'].get('dateTime', e['start'].get('date'))
        summary = e.get('summary', 'Unknown')
        context_text += f"- {summary} ({start})\n"
    
    # 2. TASKS
    tasks = storage.load_from_drive(creds, 'tasks', [])
    open_tasks = [t for t in tasks if t.get('status') != 'completed']
    
    context_text += "\n📝 ACTIVE TASKS:\n"
    if not open_tasks: context_text += "- All cleared.\n"
    for t in open_tasks:
        context_text += f"- {t['name']} (Prio: {t.get('energy', 'mid')}, Deadline: {t.get('deadline', '-')})\n"

    return context_text

# --- UI ---
st.title("Kairos Assistant 💬")
st.caption("Voice & Text Interface Active.")

# Chat History anzeigen
for msg in st.session_state.full_chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- INPUT AREA (TEXT & VOICE) ---
# Wir bauen zwei Wege für Input:
user_input = None

# 1. Voice Input (Neu!)
audio_value = st.audio_input("🎙️ Record Voice Command")

if audio_value:
    # Speichern und transkribieren
    with st.spinner("Transcribing..."):
        # Temporär speichern
        with open("temp_voice.wav", "wb") as f:
            f.write(audio_value.getvalue())
        
        # Whisper API aufrufen
        text = audio.transcribe_audio("temp_voice.wav")
        if text:
            user_input = text

# 2. Text Input (Standard)
if not user_input:
    user_input = st.chat_input("Type a message...")

# --- PROCESSING ---
if user_input:
    # 1. User Message anzeigen
    # Prüfen, ob wir die letzte Nachricht nicht doppelt senden (Audio Input bleibt manchmal im State)
    last_msg = st.session_state.full_chat_history[-1]['content'] if st.session_state.full_chat_history else ""
    
    if user_input != last_msg:
        st.session_state.full_chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 2. AI Antwort
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                live_context = get_system_context()
                
                system_msg = f"""
                You are Kairos, a hyper-intelligent productivity OS.
                
                LIVE DATA:
                {live_context}
                
                RULES:
                - Answer in ENGLISH.
                - Be concise.
                - If the user used Voice Input, be conversational.
                """
                
                messages = [{"role": "system", "content": system_msg}]
                messages.extend(st.session_state.full_chat_history[-10:])
                
                try:
                    stream = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        stream=True
                    )
                    response = st.write_stream(stream)
                    
                    st.session_state.full_chat_history.append({"role": "assistant", "content": response})
                    storage.save_to_drive(creds, 'chat_history', st.session_state.full_chat_history)
                    
                except Exception as e:
                    st.error(f"Error: {e}")

# Sidebar Clear Button
with st.sidebar:
    st.markdown("---")
    if st.button("🗑️ Clear History"):
        st.session_state.full_chat_history = []
        storage.save_to_drive(creds, 'chat_history', [])
        st.rerun()