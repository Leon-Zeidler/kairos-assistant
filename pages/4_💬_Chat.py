import streamlit as st
import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv
from modules import auth, storage, mail_agent, brain, ui

st.set_page_config(page_title="AI Chat", page_icon="💬", layout="wide")
ui.load_css()
load_dotenv()

# --- SETUP ---
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None
creds = auth.get_creds()
service = auth.get_service()

# --- DATEN LADEN (HISTORY) ---
# Wir laden den Verlauf aus der Cloud, nicht nur aus der Session
if 'full_chat_history' not in st.session_state:
    st.session_state.full_chat_history = storage.load_from_drive(creds, 'chat_history', [])

# --- KONTEXT SAMMELN (Das Gehirn) ---
@st.cache_data(ttl=300) # Alle 5 Min neu laden
def get_system_context():
    """Sammelt alle Infos für die KI"""
    context_text = f"Current Date: {datetime.datetime.now().strftime('%A, %B %d, %Y')}.\n\n"
    
    # 1. KALENDER (Nächste 3 Tage)
    now = datetime.datetime.now()
    t_min = now.isoformat() + 'Z'
    t_max = (now + datetime.timedelta(days=3)).isoformat() + 'Z'
    events = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True, orderBy='startTime').execute().get('items', [])
    
    context_text += "📅 CALENDAR (Next 3 days):\n"
    if not events: context_text += "- Keine Termine.\n"
    for e in events:
        start = e['start'].get('dateTime', e['start'].get('date'))
        summary = e.get('summary', 'Unbekannt')
        context_text += f"- {summary} ({start})\n"
    
    # 2. TASKS
    tasks = storage.load_from_drive(creds, 'tasks', [])
    open_tasks = [t for t in tasks if t.get('status') != 'completed']
    
    context_text += "\n📝 ACTIVE MISSIONS:\n"
    if not open_tasks: context_text += "- Alles erledigt.\n"
    for t in open_tasks:
        context_text += f"- {t['name']} (Prio: {t.get('energy', 'mid')}, Frist: {t.get('deadline', '-')})\n"

    # 3. EMAILS (Nur ungelesene Header)
    try:
        mails = mail_agent.fetch_unread_emails(creds, max_results=5)
        context_text += "\n📧 UNGELESENE MAILS:\n"
        if not mails: context_text += "- Inbox leer.\n"
        for m in mails:
            context_text += f"- Von: {m.get('sender', '?')} | Betreff: {m['subject']}\n"
    except:
        context_text += "\n📧 MAILS: Zugriff nicht möglich.\n"

    return context_text

# --- UI ---
st.title("Kairos Assistant")
st.caption("I know your schedule. Ask me anything.")

# Chat Verlauf anzeigen
for msg in st.session_state.full_chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# INPUT
if prompt := st.chat_input("What's on the agenda?"):
    # 1. User Nachricht anzeigen
    st.session_state.full_chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. KI Antwort generieren
    with st.chat_message("assistant"):
        with st.spinner("Analysiere Daten..."):
            # System Prompt mit Live-Daten
            live_context = get_system_context()
            
            system_msg = f"""
            You are Kairos, a hyper-intelligent productivity OS.
            
            HIER SIND DEINE LIVE-DATEN VOM USER:
            {live_context}
            
            RULES:
            - Answer in ENGLISH.
            - Be concise, friendly, and professional (like a futuristic commander).
            - Use Markdown.
            - If you don't know the answer, say "I don't have that information right now."
            """
            messages = [{"role": "system", "content": system_msg}]
            # Wir nehmen nur die letzten 10 Nachrichten für den Kontext (spart Tokens)
            messages.extend(st.session_state.full_chat_history[-10:])
            
            try:
                stream = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    stream=True
                )
                response = st.write_stream(stream)
                
                # 3. Speichern
                st.session_state.full_chat_history.append({"role": "assistant", "content": response})
                storage.save_to_drive(creds, 'chat_history', st.session_state.full_chat_history)
                
            except Exception as e:
                st.error(f"Fehler: {e}")

# Sidebar Button zum Löschen
with st.sidebar:
    if st.button("🗑️ Chat leeren"):
        st.session_state.full_chat_history = []
        storage.save_to_drive(creds, 'chat_history', [])
        st.rerun()