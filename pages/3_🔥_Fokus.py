import streamlit as st
import time
from modules import storage, auth

st.set_page_config(page_title="Deep Work", page_icon="🔥")

creds = auth.get_creds()
tasks = storage.load_from_drive(creds, 'tasks', [])

st.title("🔥 Deep Work Station")
st.caption("Ablenkungen eliminieren. Fokus aktivieren.")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Mission wählen")
    task_opts = ["Freier Fokus"] + [t['name'] for t in tasks]
    active_task = st.selectbox("Woran arbeiten wir?", task_opts)
    
    duration = st.slider("Timer (Minuten)", 5, 120, 25)
    
    if st.button("▶️ START", use_container_width=True):
        st.session_state.focus_active = True
        st.session_state.focus_start = time.time()
        st.session_state.focus_duration = duration * 60

with col2:
    # Lofi Girl Embed
    st.markdown("""
    <iframe width="100%" height="300" src="https://www.youtube.com/embed/jfKfPfyJRdk?autoplay=1&mute=1" 
    title="Lofi Girl" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
    """, unsafe_allow_html=True)

st.divider()

# --- TIMER LOGIK ---
if 'focus_active' in st.session_state and st.session_state.focus_active:
    elapsed = time.time() - st.session_state.focus_start
    remaining = st.session_state.focus_duration - elapsed
    
    if remaining > 0:
        mins, secs = divmod(int(remaining), 60)
        time_str = f"{mins:02d}:{secs:02d}"
        
        # Große Anzeige
        st.markdown(f"<h1 style='text-align: center; font-size: 80px;'>{time_str}</h1>", unsafe_allow_html=True)
        st.progress(max(0.0, min(1.0, elapsed / st.session_state.focus_duration)))
        
        st.info(f"Fokus auf: **{active_task}**")
        
        # Damit der Timer runterzählt, müssen wir die App neu laden lassen
        time.sleep(1)
        st.rerun()
    else:
        st.balloons()
        st.success("Session beendet! +50 XP")
        st.session_state.focus_active = False
        if st.button("Timer Reset"):
            st.rerun()