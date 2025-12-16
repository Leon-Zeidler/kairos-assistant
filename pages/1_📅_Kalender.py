import streamlit as st
import datetime
import json
from streamlit_calendar import calendar
from modules import brain, storage, auth, ui
from openai import OpenAI
import os
from dotenv import load_dotenv

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kalender", page_icon="📅", layout="wide")
ui.load_css()
load_dotenv()

# --- STATE MANAGEMENT ---
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

# --- AI SETUP ---
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

# --- DATEN LADEN ---
service = auth.get_service()
creds = auth.get_creds()
schedule = storage.load_from_drive(creds, 'schedule', {})
event_metadata = storage.load_from_drive(creds, 'event_metadata', {})

# --- AI FUNKTION ---
def ask_ai(event_info, question):
    if not client: return "⚠️ No API Key."
    prompt = f"""
    Context: Calendar Event '{event_info['title']}' 
    Time: {event_info['start']} to {event_info['end']}
    Description: {event_info.get('desc', '-')}
    User Question: {question}
    Answer short and helpful in ENGLISH.
    """
    try:
        return client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]
        ).choices[0].message.content
    except Exception as e: return str(e)

# --- CSS: DARK CARD OVERLAY DESIGN ---
st.markdown("""
<style>
    /* 1. Das Modal selbst dunkel machen */
    div[data-testid="stDialog"] div[role="dialog"] {
        background-color: #1e293b !important; /* Slate 800 (Heller als Hintergrund) */
        color: #f8fafc !important; /* Helle Schrift */
        border-radius: 16px !important;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7) !important;
    }
    
    /* 2. Textfarben im Modal auf Hell zwingen */
    div[data-testid="stDialog"] h1, 
    div[data-testid="stDialog"] h2, 
    div[data-testid="stDialog"] h3, 
    div[data-testid="stDialog"] h4, 
    div[data-testid="stDialog"] p, 
    div[data-testid="stDialog"] span,
    div[data-testid="stDialog"] label {
        color: #f8fafc !important;
    }
    
    /* 3. Inputs dunkel machen */
    div[data-testid="stDialog"] .stTextArea textarea, 
    div[data-testid="stDialog"] .stTextInput input {
        background-color: #0f172a !important; /* Slate 900 */
        color: #f8fafc !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }
    div[data-testid="stDialog"] .stTextArea textarea:focus, 
    div[data-testid="stDialog"] .stTextInput input:focus {
        border-color: #3b82f6 !important;
    }
    
    /* 4. Chat Messages im Modal anpassen */
    div[data-testid="stDialog"] .stChatMessage {
        background-color: #0f172a !important;
    }
    div[data-testid="stChatMessageContent"] {
        color: #e2e8f0 !important;
    }
    
    /* 5. Close Button hell machen */
    div[data-testid="stDialog"] button[aria-label="Close"] {
        color: #94a3b8 !important;
    }
    div[data-testid="stDialog"] button[aria-label="Close"]:hover {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# --- DAS DUNKLE OVERLAY (DIALOG) ---
def show_event_overlay(ev):
    eid = ev['id']
    st.markdown(f"<h2 style='margin-top: -20px; color: white;'>{ev['title']}</h2>", unsafe_allow_html=True)
    
    try:
        s = ev['start'].split('T')[1][:5] if 'T' in ev['start'] else ev['start']
        e = ev['end'].split('T')[1][:5] if 'T' in ev['end'] else ev['end']
        st.markdown(f"<p style='color: #94a3b8; font-size: 0.9rem; margin-top: -10px;'>🕒 {s} - {e}</p>", unsafe_allow_html=True)
    except: pass
    
    st.markdown("---")

    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        st.markdown("<h4 style='color: #cbd5e1;'>📝 Notes & To-Do</h4>", unsafe_allow_html=True) # En
        current_note = event_metadata.get(eid, {}).get('note', "")
        new_note = st.text_area("Note", value=current_note, height=200, key=f"note_{eid}", label_visibility="collapsed", placeholder="Type here...")
        
        if st.button("Save Note", key=f"save_{eid}", type="primary"):
            if eid not in event_metadata: event_metadata[eid] = {}
            event_metadata[eid]['note'] = new_note
            storage.save_to_drive(creds, 'event_metadata', event_metadata)
            st.success("Saved!")
            st.rerun()

    with col_right:
        st.markdown("<h4 style='color: #cbd5e1;'>🤖 AI Assistant</h4>", unsafe_allow_html=True)
        
        # Chat Verlauf
        chat_cont = st.container(height=200)
        for msg in st.session_state.chat_history:
            # Manuelles Styling für Chat Bubbles im Dark Mode
            bg = "#3b82f6" if msg["role"] == "user" else "#334155"
            color = "white"
            align = "right" if msg["role"] == "user" else "left"
            chat_cont.markdown(f"<div style='background:{bg}; padding:8px 12px; border-radius:12px; margin-bottom:8px; color:{color}; text-align:{align}; width:fit-content; margin-left:{'auto' if align=='right' else '0'};'>{msg['content']}</div>", unsafe_allow_html=True)

        # Input
        if q := st.chat_input("Ask about this event...", key=f"chat_{eid}"):
            st.session_state.chat_history.append({"role": "user", "content": q})
            
            with st.spinner("..."):
                ans = ask_ai({"title": ev['title'], "start": ev['start'], "end": ev['end'], "desc": ev.get('extendedProps', {}).get('description')}, q)
                st.session_state.chat_history.append({"role": "assistant", "content": ans})
                st.rerun()

# --- CSS: KALENDER DARK MODE (Unverändert) ---
calendar_css = """
    .fc-theme-standard .fc-scrollgrid { border: none !important; }
    .fc-theme-standard td, .fc-theme-standard th { border-color: rgba(255,255,255,0.05) !important; }
    .fc-view-harness { background-color: #0f172a !important; border-radius: 12px; }
    .fc-col-header-cell { background-color: #1e293b !important; padding: 15px 0 !important; border: none !important; border-bottom: 1px solid rgba(255,255,255,0.05) !important; }
    .fc-col-header-cell-cushion { color: #94a3b8 !important; text-transform: uppercase; font-weight: 700; font-size: 0.85rem; letter-spacing: 1px; text-decoration: none !important; }
    .fc-timegrid-axis { background-color: #0f172a !important; }
    .fc-timegrid-slot-label-cushion { color: #64748b !important; font-family: 'Inter', sans-serif; font-size: 0.75rem; }
    .fc-timegrid-slot { height: 50px !important; border-bottom: 1px solid rgba(255,255,255,0.03) !important; }
    .fc-timegrid-now-indicator-line { border-color: #10b981 !important; border-width: 2px; }
    .fc-event { border: none !important; border-radius: 6px !important; padding: 2px 5px; font-weight: 600; font-size: 0.8rem; cursor: pointer; }
    .fc-event-main { color: white !important; }
    .fc-header-toolbar { margin-bottom: 1.5rem !important; padding: 0 10px; }
    .fc-button { background-color: rgba(255,255,255,0.05) !important; border: none !important; color: #94a3b8 !important; font-weight: 600; border-radius: 8px !important; }
    .fc-button-active { background-color: #3b82f6 !important; color: white !important; }
"""

# --- MAIN LAYOUT ---
c1, c2 = st.columns([1, 2])
with c1: st.title("Schedule") # En
with c2:
    # Categories in English
    st.markdown("""
    <div style="display: flex; gap: 15px; justify-content: flex-end; align-items: center; height: 100%; padding-top: 20px;">
        <span style="color:#ef4444">● School</span>
        <span style="color:#f97316">● Sport</span>
        <span style="color:#a855f7">● Coding</span>
        <span style="color:#06b6d4">● Personal</span>
        <span style="color:#10b981">● AI Plan</span>
    </div>""", unsafe_allow_html=True)

# --- EVENTS ---
d = datetime.date.today()
search_dt = datetime.datetime.combine(d, datetime.datetime.min.time())
t_min, t_max = search_dt.isoformat() + 'Z', (search_dt + datetime.timedelta(days=7)).isoformat() + 'Z'
raw_events = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True).execute().get('items', [])

cal_events = []
COLORS = {'school': '#ef4444', 'sport': '#f97316', 'coding': '#a855f7', 'personal': '#06b6d4', 'ai_planned': '#10b981'}

for e in raw_events:
    title = e.get('summary', 'Termin')
    desc = e.get('description', '')
    cat = 'personal'
    if 'Schule' in title: cat = 'school'
    elif 'Sport' in title: cat = 'sport'
    elif 'Coding' in title: cat = 'coding'
    elif 'Kairos' in desc: cat = 'ai_planned'
    
    cal_events.append({
        "id": e['id'],
        "title": title,
        "start": e['start'].get('dateTime', e['start'].get('date')),
        "end": e['end'].get('dateTime', e['end'].get('date')),
        "backgroundColor": COLORS[cat],
        "borderColor": COLORS[cat],
        "extendedProps": {"description": desc}
    })

for i in range(7):
    loop_day = search_dt + datetime.timedelta(days=i)
    for e in brain.add_school_blocks([], loop_day, schedule):
        cal_events.append({
            "id": f"school_{i}_{e['summary']}",
            "title": e['summary'],
            "start": e['start']['dateTime'],
            "end": e['end']['dateTime'],
            "backgroundColor": "rgba(239, 68, 68, 0.7)",
            "borderColor": "#ef4444",
            "display": "block",
        })

# --- KALENDER RENDERN ---
cal_return = calendar(
    events=cal_events,
    options={
        "editable": True, "selectable": True,
        "headerToolbar": {"left": "prev,next", "center": "title", "right": "timeGridWeek,timeGridDay"},
        "initialView": "timeGridWeek", 
        "slotMinTime": "06:00:00", 
        "slotMaxTime": "22:00:00", 
        "allDaySlot": False,
        "height": "auto", 
        "contentHeight": 750,
        "locale": "en", # <--- WICHTIG: ENGLISCH
        "firstDay": 1, # Monday start is still standard in ISO, keep it or change to 0 (Sunday) for US style
        "slotLabelFormat": {"hour": "numeric", "meridiem": "short", "hour12": True}, # 9AM
    },
    custom_css=calendar_css,
    callbacks=['eventClick'],
    key='my_calendar_widget'
)

# --- TRIGGER FÜR DAS DARK OVERLAY ---
if cal_return.get("eventClick"):
    clicked = cal_return["eventClick"]["event"]
    # Session State setzen für Chat
    if 'last_clicked_id' not in st.session_state or st.session_state.last_clicked_id != clicked['id']:
        st.session_state.chat_history = []
        st.session_state.last_clicked_id = clicked['id']
        
    # DAS POPUP ÖFFNEN
    show_event_overlay(clicked)