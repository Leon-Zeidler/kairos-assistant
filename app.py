import streamlit as st
import datetime
import pandas as pd
from modules import storage, auth, brain, ui # Importiert UI helper

st.set_page_config(page_title="Kairos OS", page_icon="⏳", layout="wide")

# CSS laden
ui.load_css()

def main():
    # Auth & Daten
    service = auth.get_service()
    creds = auth.get_creds()
    tasks = storage.load_from_drive(creds, 'tasks', [])
    schedule = storage.load_from_drive(creds, 'schedule', {})

    # --- KPI CALCULATIONS (Aus React übernommen) ---
    open_missions = len([t for t in tasks if t.get('status') != 'completed']) # In React: t.status !== 'completed'
    
    # Workload berechnen
    total_workload = sum([int(t.get('duration', 0)) for t in tasks if t.get('status') != 'completed'])
    workload_hrs = round(total_workload / 60)

    # Deadline Logic
    sorted_tasks = sorted([t for t in tasks if t.get('deadline')], key=lambda x: x['deadline'])
    next_deadline = sorted_tasks[0] if sorted_tasks else None
    
    deadline_text = "No deadlines"
    is_soon = False
    deadline_subtitle = "All clear"
    accent_dl = "amber"

    if next_deadline:
        deadline_subtitle = next_deadline['name']
        dl_date = datetime.datetime.strptime(next_deadline['deadline'], "%Y-%m-%d").date()
        today = datetime.date.today()
        days_until = (dl_date - today).days

        if days_until == 0:
            deadline_text = "Today!"
            is_soon = True
        elif days_until == 1:
            deadline_text = "Tomorrow"
            is_soon = True
        else:
            deadline_text = f"{days_until}d left"
            is_soon = days_until <= 2
        
        if is_soon: accent_dl = "red"

    # --- HEADER ---
    c_head1, c_head2 = st.columns([3, 1])
    with c_head1:
        st.markdown(f"""
            <h1 style='margin-bottom: 0;'>Welcome back, <span class='text-glow-green'>Commander</span>.</h1>
            <p class='text-slate'>{datetime.datetime.now().strftime('%A, %B %d, %Y')}</p>
        """, unsafe_allow_html=True)
    with c_head2:
        st.markdown("""
            <div class="glass-card" style="padding: 0.5rem 1rem; display: flex; align-items: center; gap: 0.5rem; border-color: rgba(0,255,136,0.3);">
                <div style="width: 8px; height: 8px; background-color: #00ff88; border-radius: 50%; box-shadow: 0 0 10px #00ff88;"></div>
                <span style="color: #00ff88; font-size: 0.875rem;">All Systems Online</span>
            </div>
        """, unsafe_allow_html=True)

    st.write("") # Spacer

    # --- KPI BENTO GRID ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(ui.kpi_card("Open Missions", open_missions, "Active objectives", "Target", "blue"), unsafe_allow_html=True)
    with col2:
        st.markdown(ui.kpi_card("Workload", f"{total_workload}m", f"{workload_hrs}h total load", "Clock", "green"), unsafe_allow_html=True)
    with col3:
        st.markdown(ui.kpi_card("Next Deadline", deadline_text, deadline_subtitle, "Calendar", accent_dl), unsafe_allow_html=True)
    with col4:
        st.markdown(ui.kpi_card("System Status", "Online", "Operational", "Wifi", "green"), unsafe_allow_html=True)

    st.write("") # Spacer

    # --- MAIN CONTENT SPLIT (Agenda & Quick Actions) ---
    c_main, c_side = st.columns([2, 1])

    # LEFT: Today Agenda (Timeline View)
    with c_main:
        st.markdown('<div class="glass-card" style="height: 100%;">', unsafe_allow_html=True)
        st.subheader("Today's Agenda")
        
        # Events holen
        now = datetime.datetime.now()
        t_min = now.replace(hour=0, minute=0).isoformat() + 'Z'
        t_max = now.replace(hour=23, minute=59).isoformat() + 'Z'
        events = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True, orderBy='startTime').execute().get('items', [])
        
        # Timeline generieren
        hours = range(8, 20) # 08:00 bis 19:00
        
        for h in hours:
            # Check for events in this hour
            events_in_hour = []
            for e in events:
                start = e['start'].get('dateTime', e['start'].get('date'))
                if start and f"T{h:02d}" in start:
                    events_in_hour.append(e)
            
            # HTML Row
            ev_html = ""
            if not events_in_hour:
                ev_html = '<div style="height: 1px; width: 100%; border-bottom: 1px dashed rgba(255,255,255,0.1); margin-top: 10px;"></div>'
            else:
                for ev in events_in_hour:
                    color_bg = "rgba(0, 212, 255, 0.1)"
                    color_border = "rgba(0, 212, 255, 0.3)"
                    if "Kairos" in ev.get('description', ''):
                        color_bg = "rgba(0, 255, 136, 0.1)"
                        color_border = "rgba(0, 255, 136, 0.3)"
                    
                    ev_html += f"""
                    <div style="background: {color_bg}; border: 1px solid {color_border}; padding: 4px 8px; border-radius: 6px; margin-bottom: 4px; font-size: 0.85rem;">
                        {ev['summary']}
                    </div>
                    """

            st.markdown(f"""
            <div style="display: flex; gap: 1rem; margin-bottom: 0.5rem; align-items: flex-start;">
                <div style="font-family: monospace; color: #64748b; font-size: 0.75rem; width: 40px; padding-top: 4px;">{h:02d}:00</div>
                <div style="flex: 1; border-left: 2px solid rgba(255,255,255,0.1); padding-left: 1rem; position: relative;">
                    <div style="position: absolute; left: -5px; top: 6px; width: 8px; height: 8px; background: #1e293b; border: 2px solid #475569; border-radius: 50%;"></div>
                    {ev_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # RIGHT: Quick Actions
    with c_side:
        st.markdown('<div class="glass-card" style="height: 100%;">', unsafe_allow_html=True)
        st.subheader("Quick Actions")
        
        # Custom Buttons mit CSS
        if st.button("🔥 Start Deep Focus", use_container_width=True):
            st.switch_page("pages/3_🔥_Focus.py")
        
        st.write("")
        
        if st.button("📝 Add New Mission", use_container_width=True):
            st.switch_page("pages/2_📝_Aufgaben.py")
            
        st.write("")
        
        if st.button("✨ AI Schedule", use_container_width=True):
            # Hier könnte der Auto-Planner direkt laufen
            st.toast("AI calculating optimal path...")
            
        st.divider()
        st.markdown("""
            <div style="display: flex; justify-content: space-between; font-size: 0.875rem;">
                <span class="text-slate">Today's XP</span>
                <span style="color: #ffb800; font-weight: bold;">+120 XP</span>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == '__main__':
    main()