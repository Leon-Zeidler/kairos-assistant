import streamlit as st
import datetime
import pandas as pd
from modules import storage, brain, auth # Import aus dem neuen Ordner!

st.set_page_config(page_title="Kairos OS", page_icon="⏳", layout="wide")

def main():
    # Zentrale Auth nutzen
    service = auth.get_service('calendar', 'v3')
    creds = auth.get_creds()
    
    # DATEN LADEN
    with st.spinner("System boot..."):
        tasks = storage.load_from_drive(creds, 'tasks', [])
        schedule = storage.load_from_drive(creds, 'schedule', {})
    
    # --- DASHBOARD HEADER ---
    st.title("👋 Willkommen, Commander.")
    
    # --- KPI METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    
    open_tasks = len(tasks)
    total_minutes = sum([int(t['duration']) for t in tasks])
    
    # Nächste Deadline finden
    sorted_tasks = sorted([t for t in tasks if t.get('deadline')], key=lambda x: x['deadline'])
    next_dl = sorted_tasks[0]['deadline'] if sorted_tasks else "Keine"
    
    # Farbe für Deadline (Rot wenn heute/morgen)
    dl_delta_color = "normal"
    if next_dl != "Keine":
        dl_dt = datetime.datetime.strptime(next_dl, "%Y-%m-%d").date()
        if dl_dt <= datetime.date.today() + datetime.timedelta(days=1):
            dl_delta_color = "inverse"

    col1.metric("Offene Missionen", open_tasks)
    col2.metric("Workload", f"{total_minutes} Min")
    col3.metric("Nächste Deadline", next_dl, delta_color=dl_delta_color)
    col4.metric("System Status", "Online 🟢")

    st.markdown("---")

    # --- HEUTIGE ÜBERSICHT ---
    c_left, c_right = st.columns([2, 1])
    
    with c_left:
        st.subheader("📅 Live Feed (Heute)")
        now = datetime.datetime.now()
        t_min = now.replace(hour=0, minute=0).isoformat() + 'Z'
        t_max = now.replace(hour=23, minute=59).isoformat() + 'Z'
        events = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True, orderBy='startTime').execute().get('items', [])
        
        # Brain Logik anwenden (Schule anzeigen)
        today_events = brain.add_school_blocks(events, now, schedule)

        if not today_events:
            st.info("Keine Termine. Ruhemodus aktiv.")
        else:
            for e in today_events:
                if 'start' not in e: continue
                
                # Zeit parsen
                s_raw = e['start'].get('dateTime', e['start'].get('date'))
                dt_start = brain.parse_time(s_raw)
                
                # Visualisierung
                is_past = dt_start < now
                state_icon = "✅" if is_past else "⭕"
                is_fake = "🏫" if e.get('is_fake') else ""
                
                # Style
                if is_past:
                    st.write(f"~~{dt_start.strftime('%H:%M')} | {state_icon} {is_fake} {e['summary']}~~")
                else:
                    st.write(f"**{dt_start.strftime('%H:%M')}** | {state_icon} {is_fake} **{e['summary']}**")

    with c_right:
        st.subheader("🚀 Schnellzugriff")
        st.info("Wähle ein Modul aus der Seitenleiste links.")
        
        # Top 3 Tasks anzeigen
        if tasks:
            st.markdown("**Top Priorität:**")
            for t in tasks[:3]:
                st.caption(f"▫️ {t['name']}")

if __name__ == '__main__':
    main()