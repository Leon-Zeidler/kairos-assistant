import streamlit as st
import datetime
import os.path
import json 
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from streamlit_calendar import calendar  # <--- NEU: Das Kalender-Modul

# --- EIGENE MODULE ---
import brain
import planner
import mail_agent
import storage 

# --- KONFIGURATION ---
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive.file'
]
st.set_page_config(page_title="Kairos", page_icon="⏳", layout="wide")

# State Init
if 'suggested_slot' not in st.session_state: st.session_state.suggested_slot = None
if 'tasks' not in st.session_state: st.session_state.tasks = []

# --- GOOGLE CONNECTION (Universal) ---
def get_calendar_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    elif os.getenv("GOOGLE_TOKEN_JSON"):
        token_info = json.loads(os.getenv("GOOGLE_TOKEN_JSON"))
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)
    else:
        try:
            if st.secrets and "token_json" in st.secrets:
                token_info = json.loads(st.secrets["token_json"])
                creds = Credentials.from_authorized_user_info(token_info, SCOPES)
        except: pass

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        if not os.getenv("GOOGLE_TOKEN_JSON"):
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            
    return build('calendar', 'v3', credentials=creds)

# --- HELPER ---
def create_google_event(service, start_dt, end_dt, summary, desc=""):
    service.events().insert(calendarId='primary', body={
        'summary': summary, 'description': desc,
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Europe/Berlin'},
        'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Europe/Berlin'}
    }).execute()

def sync_week_to_google(service, schedule, ref_date):
    start = ref_date - datetime.timedelta(days=ref_date.weekday())
    c = 0
    for i in range(5):
        d = start + datetime.timedelta(days=i)
        cfg = schedule.get(str(i))
        if cfg and cfg['active'] and cfg['end'] > cfg['start']:
            s = datetime.datetime.combine(d, datetime.time(cfg['start'],0))
            e = datetime.datetime.combine(d, datetime.time(cfg['end'],0))
            create_google_event(service, s, e, "🏫 Schule [Kairos]", "Sync")
            c += 1
    return c

def collect_week_slots(service, schedule, start_date, days_to_scan=5):
    all_slots = []
    now_real = datetime.datetime.now()
    for i in range(days_to_scan):
        current_day = start_date + datetime.timedelta(days=i)
        t_min = current_day.isoformat() + 'Z'
        t_max = (current_day + datetime.timedelta(days=1)).isoformat() + 'Z'
        res = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True).execute()
        g_events = res.get('items', [])
        mixed_events = brain.add_school_blocks(g_events, current_day, schedule)
        day_slots = brain.find_free_slots(mixed_events, current_day, current_now=now_real)
        all_slots.extend(day_slots)
    return all_slots

# --- MAIN ---
def main():
    service = get_calendar_service()
    creds = service._http.credentials 
    
    # DATEN LADEN (Cloud)
    default_schedule = {str(i): {'start':8,'end':14,'active':True} for i in range(5)}
    with st.spinner("Lade Kairos Gedächtnis..."):
        schedule = storage.load_from_drive(creds, 'schedule', default_schedule)
        tasks = storage.load_from_drive(creds, 'tasks', [])

    # HEADER
    now = datetime.datetime.now()
    st.title("⏳ Kairos Hub")
    st.caption(f"Online Modus | {now.strftime('%H:%M')} Uhr")

    # SIDEBAR
    with st.sidebar:
        st.header("Einstellungen")
        with st.expander("🏫 Stundenplan"):
            days = ["Mo", "Di", "Mi", "Do", "Fr"]
            changed = False
            for i, d in enumerate(days):
                k = str(i)
                if k not in schedule: schedule[k] = {'start':8,'end':14,'active':True}
                act = st.checkbox(d, schedule[k]['active'], key=f"a{i}")
                if act:
                    times = st.slider(f"{d} Zeit", 7, 18, (schedule[k]['start'], schedule[k]['end']), key=f"t{i}")
                    if schedule[k]['start'] != times[0] or schedule[k]['end'] != times[1]:
                        schedule[k]['start'], schedule[k]['end'] = times[0], times[1]
                        changed = True
                if schedule[k]['active'] != act:
                    schedule[k]['active'] = act
                    changed = True
            if changed:
                storage.save_to_drive(creds, 'schedule', schedule)
                st.success("Gespeichert!")
        
        if st.button("🔄 Sync Woche auf Handy"):
            n = sync_week_to_google(service, schedule, datetime.date.today())
            st.success(f"{n} Termine!")

    # VIEW SETUP
    col_d1, col_d2 = st.columns([1,3])
    with col_d1:
        view_date = st.date_input("Ansicht:", datetime.date.today())
    search_dt = datetime.datetime.combine(view_date, datetime.datetime.min.time())

    # EVENTS HOLEN
    t_min = search_dt.isoformat() + 'Z'
    t_max = (search_dt + datetime.timedelta(days=1)).isoformat() + 'Z'
    ev_res = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True, orderBy='startTime').execute()
    today_events = brain.add_school_blocks(ev_res.get('items', []), search_dt, schedule)
    
    # --- KALENDER VORBEREITEN ---
    calendar_events = []
    for e in today_events:
        if 'start' not in e: continue
        
        # Farben zuweisen
        color = "#3788d8" # Standard Blau
        if e.get('is_fake'): color = "#ff4b4b" # Rot (Schule)
        elif "Kairos" in e.get('summary', ''): color = "#00c853" # Grün (KI)

        calendar_events.append({
            "title": e['summary'],
            "start": e['start'].get('dateTime', e['start'].get('date')),
            "end": e['end'].get('dateTime', e['end'].get('date')),
            "color": color,
        })

    cal_options = {
        "headerToolbar": {"left": "today", "center": "title", "right": "timeGridDay,timeGridWeek"},
        "initialView": "timeGridDay",
        "initialDate": view_date.isoformat(),
        "slotMinTime": "06:00:00",
        "slotMaxTime": "22:00:00",
        "height": 650,
        "allDaySlot": False,
    }

    # --- LAYOUT ANZEIGE ---
    c_left, c_right = st.columns([2, 1])
    
    with c_left:
        st.subheader("📅 Dein Tag")
        calendar(events=calendar_events, options=cal_options)

    with c_right:
        st.subheader("📝 Aufgaben")
        
        with st.form("new_task_form", clear_on_submit=True):
            c1, c2 = st.columns([2,1])
            tn = c1.text_input("Titel")
            td = c2.number_input("Min", value=45, step=15)
            cc, cd = st.columns([1,2])
            use_dl = cc.checkbox("Deadline?")
            dl_date = cd.date_input("Bis", datetime.date.today() + datetime.timedelta(days=2))
            
            if st.form_submit_button("➕"):
                if tn:
                    fdl = dl_date.strftime("%Y-%m-%d") if use_dl else None
                    tasks.append({"name": tn, "duration": td, "deadline": fdl})
                    storage.save_to_drive(creds, 'tasks', tasks)
                    st.rerun()

        st.markdown("---")
        if not tasks: st.caption("Leer.")
        
        for i, task in enumerate(tasks):
            dd = f"🚨 {task['deadline']}" if task.get('deadline') else ""
            with st.expander(f"{task['name']} ({task['duration']}m) {dd}"):
                c_b1, c_b2 = st.columns(2)
                if c_b1.button("✨ Planen", key=f"p_{i}"):
                    with st.spinner("Suche Slot..."):
                        ws = collect_week_slots(service, schedule, datetime.datetime.now(), 5)
                        prop = planner.suggest_slot(f"{task['name']} ({task['duration']}m)", ws, task.get('deadline'))
                        st.session_state.suggested_slot = prop
                        st.session_state.task_to_remove = i
                        st.rerun()
                if c_b2.button("🗑️", key=f"d_{i}"):
                    tasks.pop(i)
                    storage.save_to_drive(creds, 'tasks', tasks)
                    st.rerun()

    # POPUP
    if st.session_state.suggested_slot:
        st.divider()
        p = st.session_state.suggested_slot
        if p.get("found"):
            st.success(f"Vorschlag: {p['reason']}")
            st.info(f"📅 {p['new_start_time']} - {p['new_end_time']}")
            co, cn = st.columns(2)
            if co.button("✅ Buchen"):
                s = datetime.datetime.strptime(p['new_start_time'], "%Y-%m-%d %H:%M")
                e = datetime.datetime.strptime(p['new_end_time'], "%Y-%m-%d %H:%M")
                create_google_event(service, s, e, p['summary'], "Kairos Auto-Plan")
                if st.session_state.task_to_remove is not None:
                    if st.session_state.task_to_remove < len(tasks):
                        tasks.pop(st.session_state.task_to_remove)
                        storage.save_to_drive(creds, 'tasks', tasks)
                    st.session_state.task_to_remove = None
                st.session_state.suggested_slot = None
                st.balloons()
                st.rerun()
            if cn.button("Abbrechen"):
                st.session_state.suggested_slot = None
                st.rerun()
        else:
            st.error(p.get('reason'))
            if st.button("Ok"): 
                st.session_state.suggested_slot = None
                st.rerun()
    
    with st.expander("📧 Inbox"):
        if st.button("Check"):
            ms = mail_agent.fetch_unread_emails(creds)
            if not ms: st.info("Leer.")
            for m in ms:
                st.write(f"📩 {m['subject']}")
                if st.button("Als Task", key=m['subject']):
                    tasks.append({"name": m['ai_data']['summary'], "duration": 60, "deadline": None})
                    storage.save_to_drive(creds, 'tasks', tasks)

if __name__ == '__main__':
    main()