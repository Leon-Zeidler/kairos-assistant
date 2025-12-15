import streamlit as st
import time
from modules import storage, auth, ui

st.set_page_config(page_title="Deep Focus", page_icon="🔥", layout="wide")
ui.load_css()

# Custom CSS für den Timer Ring (SVG Animation Imitation)
st.markdown("""
<style>
@keyframes pulse-ring {
    0% { box-shadow: 0 0 0 0 rgba(0, 255, 136, 0.4); }
    70% { box-shadow: 0 0 0 20px rgba(0, 255, 136, 0); }
    100% { box-shadow: 0 0 0 0 rgba(0, 255, 136, 0); }
}
.timer-container {
    width: 300px; height: 300px;
    border-radius: 50%;
    border: 4px solid rgba(255,255,255,0.05);
    display: flex; justify-content: center; align-items: center;
    margin: 0 auto;
    position: relative;
}
.timer-active {
    border-color: #00ff88;
    animation: pulse-ring 2s infinite;
    box-shadow: 0 0 30px rgba(0,255,136,0.2);
}
.timer-text { font-size: 4rem; font-family: monospace; font-weight: bold; color: white; }
.timer-label { position: absolute; bottom: 60px; font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 2px; }
</style>
""", unsafe_allow_html=True)

# HEADER
c1, c2 = st.columns([1, 1])
with c1:
    st.markdown('<h1>Deep Focus</h1><p class="text-slate">Enter the flow state</p>', unsafe_allow_html=True)

# SESSION STATE
if 'focus_running' not in st.session_state: st.session_state.focus_running = False
if 'time_left' not in st.session_state: st.session_state.time_left = 25 * 60

# MAIN LAYOUT
col_timer, col_media = st.columns([2, 1])

with col_timer:
    st.markdown('<div class="glass-card" style="text-align: center; height: 100%;">', unsafe_allow_html=True)
    
    # Task Selector
    creds = auth.get_creds()
    tasks = storage.load_from_drive(creds, 'tasks', [])
    task_opts = ["Freier Fokus"] + [t['name'] for t in tasks]
    sel_task = st.selectbox("Select Mission", task_opts)
    
    # Duration Buttons
    cols = st.columns(4)
    if cols[0].button("15m"): st.session_state.time_left = 15*60
    if cols[1].button("25m"): st.session_state.time_left = 25*60
    if cols[2].button("45m"): st.session_state.time_left = 45*60
    if cols[3].button("60m"): st.session_state.time_left = 60*60
    
    st.write("")
    
    # TIMER VISUALIZATION
    mins, secs = divmod(st.session_state.time_left, 60)
    timer_cls = "timer-active" if st.session_state.focus_running else ""
    glow_color = "#00ff88" if st.session_state.focus_running else "#00d4ff"
    
    st.markdown(f"""
    <div class="timer-container {timer_cls}" style="border-color: {glow_color};">
        <div style="text-align: center;">
            <div class="timer-text" style="color: {glow_color}; text-shadow: 0 0 20px {glow_color};">
                {mins:02d}:{secs:02d}
            </div>
            <div class="timer-label">{ "IN PROGRESS" if st.session_state.focus_running else "READY" }</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    st.write("")
    
    # CONTROLS
    c_play, c_reset = st.columns(2)
    if c_play.button("⏯️ Start / Pause", use_container_width=True):
        st.session_state.focus_running = not st.session_state.focus_running
        
    if c_reset.button("🔄 Reset", use_container_width=True):
        st.session_state.focus_running = False
        st.session_state.time_left = 25 * 60
        st.rerun()

    # TIMER LOGIC (Streamlit Loop Hack)
    if st.session_state.focus_running and st.session_state.time_left > 0:
        time.sleep(1)
        st.session_state.time_left -= 1
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

with col_media:
    # Lofi Card
    st.markdown("""
    <div class="glass-card">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
            <div style="padding: 4px; background: rgba(168, 85, 247, 0.2); border-radius: 4px;">🎵</div>
            <span style="font-weight: bold;">Ambient Sound</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.video("https://www.youtube.com/watch?v=jfKfPfyJRdk")
    
    st.markdown("""
    <div class="glass-card" style="margin-top: 1rem;">
        <h3 style="font-size: 1rem;">Focus Tips</h3>
        <ul style="font-size: 0.8rem; color: #94a3b8; padding-left: 1rem;">
            <li>Put phone in another room</li>
            <li>Close unnecessary tabs</li>
            <li>Stay hydrated 💧</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)