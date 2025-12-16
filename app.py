import streamlit as st
import datetime
from modules import storage, auth, brain, ui, audio

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kairos OS", page_icon="⚡", layout="wide")

# --- SIDEBAR & ROUTING ---
# Das rendert die Sidebar UND leitet automatisch weiter.
# Wir speichern das Ergebnis in 'selected_page', falls wir es für Logik brauchen,
# aber wir brauchen keinen if/elif Block mehr für switch_page.
selected_page = ui.render_sidebar(active_page="Dashboard")

# --- HELPER: HABIT TRACKER ---
def load_habits(creds):
    defaults = {
        "📖 Reading (10m)": {},
        "💧 Water (2L)": {},
        "🏋️ Sport / Gym": {}
    }
    return storage.load_from_drive(creds, 'habits', defaults)

def render_habit_tracker(creds):
    habits = load_habits(creds)
    today_str = datetime.date.today().isoformat()
    
    st.subheader("🔥 Habit Tracker")
    
    cols = st.columns(len(habits))
    updated = False
    
    for i, (habit_name, history) in enumerate(habits.items()):
        # Streak berechnen
        streak = 0
        check_date = datetime.date.today()
        if not history.get(today_str, False):
            check_date -= datetime.timedelta(days=1)
            
        while check_date.isoformat() in history and history[check_date.isoformat()]:
            streak += 1
            check_date -= datetime.timedelta(days=1)
            
        is_done = history.get(today_str, False)
        
        # Styles
        bg = "rgba(16, 185, 129, 0.1)" if is_done else "rgba(255,255,255,0.03)"
        border = "#10b981" if is_done else "rgba(255,255,255,0.1)"
        text_c = "#10b981" if is_done else "#94a3b8"
        icon = "🔥" if streak > 0 else "❄️"
        
        with cols[i]:
            st.markdown(f"""
            <div style="background:{bg}; border:1px solid {border}; border-radius:12px; padding:15px; text-align:center; transition: all 0.3s;">
                <div style="font-weight:600; color:white; margin-bottom:5px; font-size:0.9rem;">{habit_name}</div>
                <div style="font-size:1.8rem; font-weight:bold; color:white;">{icon} {streak}</div>
                <div style="font-size:0.75rem; color:{text_c}; text-transform:uppercase; letter-spacing:1px;">Day Streak</div>
            </div>
            """, unsafe_allow_html=True)
            
            check_val = st.checkbox("Done", value=is_done, key=f"habit_{i}", label_visibility="collapsed")
            if check_val != is_done:
                habits[habit_name][today_str] = check_val
                updated = True
    
    if updated:
        storage.save_to_drive(creds, 'habits', habits)
        st.rerun()

# --- DASHBOARD VIEW ---
# Wir zeigen das Dashboard nur an, wenn wir NICHT woanders hinnavigieren
if selected_page == "Dashboard":
    
    # Auth & Data Load
    creds = auth.get_creds()
    tasks = storage.load_from_drive(creds, 'tasks', [])
    service = auth.get_service()

    # Greeting Logic
    hour = datetime.datetime.now().hour
    greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 18 else "Good Evening"
    
    # --- HEADER SECTION ---
    c_head1, c_head2 = st.columns([3, 1])
    with c_head1:
        st.markdown(f"# {greeting}, Commander.")
        st.markdown(f"<p style='color: #94a3b8; margin-top: -15px;'>System online. Ready for command.</p>", unsafe_allow_html=True)
    
    # --- AUDIO BRIEFING BUTTON ---
    with c_head2:
        if st.button("🔊 Play Briefing", use_container_width=True):
            with st.spinner("Generating Audio Report..."):
                # Daten sammeln für das Briefing
                date_str = datetime.datetime.now().strftime("%A, %d %B")
                open_tasks_count = len([t for t in tasks if t.get('status') != 'completed'])
                
                # Events holen
                now = datetime.datetime.now()
                t_min = now.replace(hour=0, minute=0).isoformat() + 'Z'
                t_max = now.replace(hour=23, minute=59).isoformat() + 'Z'
                day_events = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True).execute().get('items', [])
                
                event_msg = f"You have {len(day_events)} events on your calendar."
                if day_events:
                    first = day_events[0]
                    # Sicherstellen dass 'dateTime' existiert (bei ganztägigen Events gibt es nur 'date')
                    start_raw = first['start'].get('dateTime', first['start'].get('date'))
                    t = brain.parse_time(start_raw)
                    event_msg += f" The first one is {first['summary']} at {t.strftime('%I:%M %p')}."

                # Text für TTS
                speech_text = f"""
                {greeting}. Today is {date_str}. 
                Here is your status report. 
                {event_msg}
                You currently have {open_tasks_count} active missions waiting. 
                All systems are nominal. Good luck.
                """
                
                # Audio generieren
                audio_path = audio.generate_audio_briefing(speech_text)
                if audio_path:
                    st.audio(audio_path, format="audio/mp3", autoplay=True)

    st.write("") 

    # --- KPI CARDS ---
    open_tasks = len([t for t in tasks if t.get('status') != 'completed'])
    total_mins = sum([int(t.get('duration', 0)) for t in tasks if t.get('status') != 'completed'])
    
    sorted_tasks = sorted([t for t in tasks if t.get('deadline')], key=lambda x: x['deadline'])
    dl_name = "No deadlines"
    dl_info = "Clear"
    if sorted_tasks:
        dl_name = sorted_tasks[0]['name']
        d = datetime.datetime.strptime(sorted_tasks[0]['deadline'], "%Y-%m-%d").date()
        diff = (d - datetime.date.today()).days
        dl_info = f"in {diff} days" if diff > 1 else "⚠️ Tomorrow" if diff == 1 else "🚨 TODAY"

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(ui.card("Open Tasks", str(open_tasks), "Pending", "⚡"), unsafe_allow_html=True)
    with c2: st.markdown(ui.card("Workload", f"{total_mins}m", "Scheduled", "⏱️"), unsafe_allow_html=True)
    with c3: st.markdown(ui.card("Priority", dl_name[:15]+"..." if len(dl_name)>15 else dl_name, dl_info, "🔥"), unsafe_allow_html=True)
    with c4: st.markdown(ui.card("System Status", "Online", "V 2.3", "🟢"), unsafe_allow_html=True)

    st.markdown("---")
    
    # --- HABIT TRACKER ---
    render_habit_tracker(creds)
    
    st.markdown("---")
    
    # --- TIMELINE & QUICK ACTIONS ---
    col_main, col_side = st.columns([2, 1], gap="large")
    
    with col_main:
        st.subheader("📅 Timeline")
        now = datetime.datetime.now()
        t_min = now.replace(hour=0, minute=0).isoformat() + 'Z'
        t_max = now.replace(hour=23, minute=59).isoformat() + 'Z'
        events = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True, orderBy='startTime').execute().get('items', [])
        
        if not events:
            st.info("🎉 Free day! No events scheduled.")
        else:
            for e in events:
                start = e['start'].get('dateTime', e['start'].get('date'))
                if not start: continue
                dt = brain.parse_time(start)
                
                # Timezone fix
                is_past = dt < now.astimezone()
                
                opacity = "0.5" if is_past else "1.0"
                border_color = "#3b82f6" if not is_past else "#475569"
                time_str = dt.strftime('%I:%M %p')
                
                st.markdown(f"""
                <div style="display: flex; gap: 15px; margin-bottom: 12px; opacity: {opacity}; align-items: center; background: rgba(255,255,255,0.03); padding: 12px; border-radius: 12px; border-left: 4px solid {border_color};">
                    <div style="font-weight: 700; color: #fff; font-family: monospace; width: 80px;">{time_str}</div>
                    <div style="color: #cbd5e1;">{e['summary']}</div>
                </div>""", unsafe_allow_html=True)

    with col_side:
        st.subheader("Quick Actions")
        if st.button("🔥 Focus Mode", use_container_width=True):
            st.switch_page("pages/3_🔥_Focus.py")
            
        st.write("")
        if st.button("➕ Add Task", use_container_width=True):
            st.switch_page("pages/2_📝_Tasks.py")
            
        st.write("")
        with st.expander("💡 Daily Quote"):
            st.caption('"The best way to predict the future is to create it."')