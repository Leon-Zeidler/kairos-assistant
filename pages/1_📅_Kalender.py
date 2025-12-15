import streamlit as st
import datetime
from streamlit_calendar import calendar
from modules import brain, storage, auth # Wichtig: Import aus modules

st.set_page_config(page_title="Kalender", page_icon="📅", layout="wide")

# Auth
service = auth.get_service()
creds = auth.get_creds()

# Daten
schedule = storage.load_from_drive(creds, 'schedule', {})

st.title("📅 Master Kalender")

# Controls
col_view, col_date = st.columns([1, 2])
view_mode = col_view.radio("Ansicht", ["Tag", "Woche"], horizontal=True)
view_date = col_date.date_input("Datum", datetime.date.today())

search_dt = datetime.datetime.combine(view_date, datetime.datetime.min.time())

# Zeitraum berechnen
if view_mode == "Tag":
    days = 1
    initial_view = "timeGridDay"
else:
    days = 7
    initial_view = "timeGridWeek"

t_min = search_dt.isoformat() + 'Z'
t_max = (search_dt + datetime.timedelta(days=days)).isoformat() + 'Z'

# Events laden
res = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True).execute()
raw_events = res.get('items', [])

# Brain Magic anwenden (Schule für den Zeitraum berechnen)
# Wir loopen durch die Tage, um Schule korrekt einzufügen
cal_events = []
for i in range(days):
    loop_day = search_dt + datetime.timedelta(days=i)
    # Nur Schule für diesen Tag berechnen
    day_mix = brain.add_school_blocks([], loop_day, schedule)
    for e in day_mix:
        cal_events.append({
            "title": e['summary'],
            "start": e['start']['dateTime'],
            "end": e['end']['dateTime'],
            "color": "#ff4b4b", # Rot für Schule
        })

# Google Events hinzufügen
for e in raw_events:
    color = "#3788d8"
    if "Kairos" in e.get('description', ''): color = "#00c853"
    
    cal_events.append({
        "title": e['summary'],
        "start": e['start'].get('dateTime', e['start'].get('date')),
        "end": e['end'].get('dateTime', e['end'].get('date')),
        "color": color
    })

opts = {
    "headerToolbar": {"left": "today", "center": "title", "right": ""},
    "initialView": initial_view,
    "initialDate": view_date.isoformat(),
    "slotMinTime": "06:00:00",
    "slotMaxTime": "22:00:00",
    "height": 700,
    "allDaySlot": False
}

calendar(events=cal_events, options=opts)