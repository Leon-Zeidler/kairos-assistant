import streamlit as st
import datetime
from streamlit_calendar import calendar
from modules import brain, storage, auth, ui
from openai import OpenAI
import os
from dotenv import load_dotenv

# --- PAGE CONFIG ---
st.set_page_config(page_title="Calendar", page_icon="📅", layout="wide")

# --- 1. CLEAN MODERN CSS (Professional SaaS Look) ---
st.markdown("""
    <style>
        /* --- HIDE STREAMLIT UI ELEMENTS (Menu, Header, Footer) --- */
        header[data-testid="stHeader"] {
            display: none;
        }
        div[data-testid="stDecoration"] {
            display: none;
        }
        footer {
            display: none;
        }
        
        /* Das rückt den Inhalt nach oben, da der Header weg ist */
        .block-container {
            padding-top: 1rem !important;
        }

        /* --- BACKGROUND & GLOBAL --- */
        .stApp {
            background-color: #0e1117; /* Deep Professional Dark */
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        h1, h2, h3 {
            font-weight: 600;
            letter-spacing: -0.5px;
            color: #ffffff;
        }
        
        /* --- MODERN INPUTS (No ugly grey borders) --- */
        
        div[data-baseweb="select"] > div, 
        div[data-baseweb="input"] > div {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 8px !important;
            color: white !important;
            transition: all 0.2s ease;
        }
        
        div[data-baseweb="select"] > div:focus-within,
        div[data-baseweb="input"] > div:focus-within {
            border-color: #3b82f6 !important;
            background-color: rgba(255, 255, 255, 0.08) !important;
            box-shadow: 0 0 0 1px #3b82f6;
        }

        div[data-baseweb="select"] span {
            color: #e2e8f0 !important;
        }
        
        ul[data-baseweb="menu"] {
            background-color: #1a1f2e !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3) !important;
        }
        
        div[data-baseweb="slider"] div[role="slider"] {
            background-color: white !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }
        div[data-baseweb="slider"] div {
            background-color: rgba(255, 255, 255, 0.2) !important;
        }

        /* --- CLEAN EXPANDER --- */
        .streamlit-expanderHeader {
            background-color: transparent !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            color: #e2e8f0 !important;
            font-weight: 500;
        }
        .streamlit-expanderHeader:hover {
            border-color: #3b82f6 !important;
            color: #3b82f6 !important;
        }
        .streamlit-expanderContent {
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-top: none;
            border-radius: 0 0 8px 8px !important;
            background-color: rgba(255, 255, 255, 0.02);
        }
        
        /* --- BUTTONS --- */
        .stButton button {
            background-color: #ffffff;
            color: #0f172a;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            padding: 0.5rem 1rem;
            transition: all 0.2s;
        }
        .stButton button:hover {
            background-color: #f1f5f9;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
    </style>
""", unsafe_allow_html=True)

# Standard UI laden
ui.render_sidebar("Calendar")
load_dotenv()

# --- DATA ---
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None
creds = auth.get_creds()
service = auth.get_service()
schedule = storage.load_from_drive(creds, 'schedule', {})
event_metadata = storage.load_from_drive(creds, 'event_metadata', {})

# --- SETTINGS ---
default_settings = {
    "colors": {'school': '#ef4444', 'sport': '#f97316', 'coding': '#a855f7', 'personal': '#06b6d4', 'ai_planned': '#10b981'},
    "start_hour": 6, "end_hour": 22, "view_mode": "timeGridWeek"
}
cal_settings = storage.load_from_drive(creds, 'calendar_settings', default_settings)

# --- TITLE & ACTIONS ---
c_title, c_actions = st.columns([2, 1])
with c_title:
    st.title("Calendar")

with c_actions:
    with st.expander("⚙️ View Settings", expanded=False):
        st.caption("Display Configuration")
        
        # Grid Layout für Settings
        c1, c2 = st.columns(2)
        with c1:
            new_view = st.selectbox("View", ["Week", "Day"], index=0 if cal_settings['view_mode'] == 'timeGridWeek' else 1, label_visibility="collapsed")
        with c2:
            time_range = st.slider("Hours", 0, 24, (cal_settings['start_hour'], cal_settings['end_hour']), label_visibility="collapsed")

        st.caption("Category Colors")
        cols = st.columns(5)
        new_colors = cal_settings['colors'].copy()
        
        # Loop for colors
        labels = ["School", "Sport", "Code", "Personal", "AI"]
        keys = ["school", "sport", "coding", "personal", "ai_planned"]
        
        for i, col in enumerate(cols):
            with col:
                new_colors[keys[i]] = st.color_picker(labels[i], new_colors[keys[i]], label_visibility="collapsed")
        
        if st.button("Apply Changes", use_container_width=True):
            cal_settings['colors'] = new_colors
            cal_settings['view_mode'] = "timeGridWeek" if new_view == "Week" else "timeGridDay"
            cal_settings['start_hour'] = time_range[0]
            cal_settings['end_hour'] = time_range[1]
            storage.save_to_drive(creds, 'calendar_settings', cal_settings)
            st.rerun()

st.markdown("---")

# --- EVENTS PROCESSING ---
d = datetime.date.today()
search_dt = datetime.datetime.combine(d, datetime.datetime.min.time())
t_min = search_dt.isoformat() + 'Z'
t_max = (search_dt + datetime.timedelta(days=7)).isoformat() + 'Z'
raw_events = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True).execute().get('items', [])

cal_events = []
COLORS = cal_settings['colors']

for e in raw_events:
    title = e.get('summary', 'Event')
    desc = e.get('description', '')
    cat = 'personal'
    if 'Schule' in title or 'School' in title: cat = 'school'
    elif 'Sport' in title: cat = 'sport'
    elif 'Coding' in title: cat = 'coding'
    elif 'Kairos' in desc: cat = 'ai_planned'
    
    cal_events.append({
        "id": e['id'],
        "title": title,
        "start": e['start'].get('dateTime', e['start'].get('date')),
        "end": e['end'].get('dateTime', e['end'].get('date')),
        "backgroundColor": COLORS.get(cat, COLORS['personal']),
        "borderColor": "transparent",
        "extendedProps": {"description": desc}
    })

# Add School Blocks
for i in range(7):
    loop_day = search_dt + datetime.timedelta(days=i)
    for e in brain.add_school_blocks([], loop_day, schedule):
        cal_events.append({
            "id": f"school_{i}_{e['summary']}",
            "title": e['summary'],
            "start": e['start']['dateTime'],
            "end": e['end']['dateTime'],
            "backgroundColor": COLORS['school'],
            "borderColor": "transparent",
            "extendedProps": {"description": "School"}
        })

# --- CLEAN CALENDAR CSS ---
calendar_css = """
    /* General Clean Up */
    .fc-theme-standard td, .fc-theme-standard th {
        border-color: rgba(255, 255, 255, 0.06) !important;
    }
    .fc-scrollgrid {
        border: none !important;
    }
    
    /* Header (Days) */
    .fc-col-header-cell {
        background-color: transparent !important;
        border: none !important;
        padding-bottom: 10px !important;
    }
    .fc-col-header-cell-cushion {
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 0.5px;
        text-decoration: none !important;
    }
    
    /* Timeslots */
    .fc-timegrid-slot {
        height: 50px !important; 
        border-bottom: 1px solid rgba(255, 255, 255, 0.04) !important;
    }
    .fc-timegrid-slot-label-cushion {
        color: #64748b !important;
        font-size: 0.75rem;
        font-family: monospace;
    }
    .fc-timegrid-axis {
        border: none !important;
    }
    
    /* Events */
    .fc-event {
        border-radius: 4px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        padding: 2px 4px;
        font-weight: 500;
        font-size: 0.85rem;
    }
    .fc-event:hover {
        opacity: 0.9;
    }
    
    /* Red Line */
    .fc-timegrid-now-indicator-line {
        border-color: #ef4444; 
        border-width: 1px;
    }
    .fc-timegrid-now-indicator-arrow {
        border-color: #ef4444;
        border-width: 5px;
    }
    
    /* Buttons */
    .fc-button-primary {
        background-color: rgba(255,255,255,0.05) !important;
        border: none !important;
        color: white !important;
        font-weight: 500 !important;
        text-transform: capitalize !important;
        border-radius: 6px !important;
        padding: 0.4rem 1rem !important;
    }
    .fc-button-primary:hover {
        background-color: rgba(255,255,255,0.1) !important;
    }
    .fc-button-active {
        background-color: #ffffff !important;
        color: black !important;
    }
"""

# --- RENDER ---
cal = calendar(
    events=cal_events,
    options={
        "editable": True, 
        "selectable": True,
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "timeGridWeek,timeGridDay"},
        "initialView": cal_settings['view_mode'],
        "slotMinTime": f"{cal_settings['start_hour']:02d}:00:00",
        "slotMaxTime": f"{cal_settings['end_hour']:02d}:00:00",
        "allDaySlot": False, 
        "height": "auto", 
        "contentHeight": 800, 
        "locale": "en",
        "nowIndicator": True,
        "slotLabelFormat": {"hour": "numeric", "meridiem": "short", "hour12": True},
        "dayHeaderFormat": {"weekday": "short", "day": "numeric"}
    },
    custom_css=calendar_css,
    callbacks=['eventClick'],
    key='clean_calendar'
)

# --- OVERLAY ---
@st.dialog("Event Details")
def show_overlay(ev):
    st.markdown(f"""
        <h3 style='margin:0; padding-bottom:5px; border-bottom:1px solid rgba(255,255,255,0.1);'>{ev['title']}</h3>
        <div style='color:#94a3b8; font-size:0.9rem; margin-top:10px; margin-bottom:20px;'>
            ⏱ {ev['start'].split('T')[1][:5]} - {ev['end'].split('T')[1][:5]}
        </div>
    """, unsafe_allow_html=True)
    
    eid = ev['id']
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Notes**")
        curr = event_metadata.get(eid, {}).get('note', "")
        note = st.text_area("Notes", value=curr, height=150, label_visibility="collapsed", placeholder="Add notes...")
        if st.button("Save", type="primary", use_container_width=True):
            if eid not in event_metadata: event_metadata[eid] = {}
            event_metadata[eid]['note'] = note
            storage.save_to_drive(creds, 'event_metadata', event_metadata)
            st.rerun()
            
    with col2:
        st.markdown("**AI Assistant**")
        if q := st.chat_input("Ask about this..."):
            with st.spinner("Processing..."):
                try:
                    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user", "content":f"Event: {ev['title']}. Q: {q}"}]).choices[0].message.content
                    st.info(res)
                except: st.error("Error")

if cal.get("eventClick"):
    show_overlay(cal["eventClick"]["event"])