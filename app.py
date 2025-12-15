import streamlit as st
import datetime
from modules import storage, auth, brain, ui

st.set_page_config(page_title="Kairos", page_icon="⏱️", layout="wide")
ui.load_css()

def main():
    service = auth.get_service()
    creds = auth.get_creds()
    tasks = storage.load_from_drive(creds, 'tasks', [])
    schedule = storage.load_from_drive(creds, 'schedule', {})

    # Berechnungen
    open_tasks = len([t for t in tasks if t.get('status') != 'completed'])
    total_mins = sum([int(t.get('duration', 0)) for t in tasks if t.get('status') != 'completed'])
    
    # Nächste Deadline
    sorted_tasks = sorted([t for t in tasks if t.get('deadline')], key=lambda x: x['deadline'])
    next_dl_text = "Keine"
    if sorted_tasks:
        d = datetime.datetime.strptime(sorted_tasks[0]['deadline'], "%Y-%m-%d").date()
        diff = (d - datetime.date.today()).days
        if diff == 0: next_dl_text = "Heute fällig"
        elif diff == 1: next_dl_text = "Morgen fällig"
        else: next_dl_text = f"In {diff} Tagen"

    # --- HEADER ---
    st.title(f"Guten Tag.")
    st.caption(f"Heute ist {datetime.datetime.now().strftime('%A, %d. %B')}")
    st.markdown("---")

    # --- KPI GRID (Clean) ---
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(ui.card("Offen", str(open_tasks), "Aufgaben", "📥"), unsafe_allow_html=True)
    with c2: st.markdown(ui.card("Workload", f"{total_mins}m", f"{round(total_mins/60, 1)} Stunden", "⏱️"), unsafe_allow_html=True)
    with c3: st.markdown(ui.card("Fokus", next_dl_text, sorted_tasks[0]['name'] if sorted_tasks else "-", "🎯"), unsafe_allow_html=True)
    with c4: st.markdown(ui.card("Status", "Aktiv", "System bereit", "✅"), unsafe_allow_html=True)

    st.write("") 

    # --- CONTENT ---
    col_agenda, col_quick = st.columns([2, 1])

    with col_agenda:
        st.subheader("Kalender")
        # Eine simple Liste statt Neon-Timeline
        now = datetime.datetime.now()
        t_min = now.replace(hour=0, minute=0).isoformat() + 'Z'
        t_max = now.replace(hour=23, minute=59).isoformat() + 'Z'
        events = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True, orderBy='startTime').execute().get('items', [])
        
        if not events:
            st.info("Keine Termine für heute.")
        else:
            for e in events:
                start = e['start'].get('dateTime', e['start'].get('date'))
                if not start: continue
                dt = brain.parse_time(start)
                
                # Clean visual
                with st.container():
                    c_time, c_text = st.columns([1, 5])
                    c_time.write(f"**{dt.strftime('%H:%M')}**")
                    c_text.write(e['summary'])
                    st.divider()

    with col_quick:
        st.subheader("Aktionen")
        with st.container(border=True):
            if st.button("⏱️ Fokus Session starten", use_container_width=True):
                st.switch_page("pages/3_🔥_Fokus.py")
            st.write("")
            if st.button("📝 Aufgabe hinzufügen", use_container_width=True):
                st.switch_page("pages/2_📝_Aufgaben.py")

if __name__ == '__main__':
    main()