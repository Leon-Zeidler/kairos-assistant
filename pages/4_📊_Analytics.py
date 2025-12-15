import streamlit as st
import pandas as pd
from modules import storage, auth, ui

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")
ui.load_css()

creds = auth.get_creds()
tasks = storage.load_from_drive(creds, 'tasks', [])

# Header
st.markdown('<h1>Analytics</h1><p class="text-slate">Track your productivity journey</p>', unsafe_allow_html=True)

# STATS GRID
done_tasks = len([t for t in tasks if t.get('status') == 'completed'])
total_mins = sum([int(t['duration']) for t in tasks])

c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(ui.kpi_card("Completed", done_tasks, "Total missions", "Target", "green"), unsafe_allow_html=True)
with c2: st.markdown(ui.kpi_card("Focus Time", f"{total_mins}m", "Total minutes", "Clock", "blue"), unsafe_allow_html=True)
with c3: st.markdown(ui.kpi_card("Sessions", "12", "Focus blocks", "Wifi", "purple"), unsafe_allow_html=True) # Mock Data
with c4: st.markdown(ui.kpi_card("Avg Session", "45m", "Focus span", "Target", "amber"), unsafe_allow_html=True)

st.write("")

# CHARTS (Glass Containers)
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown('<div class="glass-card"><h3>Productivity by Category</h3>', unsafe_allow_html=True)
    if tasks:
        df = pd.DataFrame(tasks)
        cat_counts = df['category'].value_counts()
        st.bar_chart(cat_counts, color="#00ff88")
    else:
        st.info("No data yet.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_chart2:
    st.markdown('<div class="glass-card"><h3>XP Progress</h3>', unsafe_allow_html=True)
    
    # XP Card Imitation
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
        <div>
            <div style="font-size: 0.8rem; color: #64748b;">Total XP</div>
            <div style="font-size: 2rem; font-weight: bold; color: #ffb800;">1,250</div>
        </div>
        <div>
            <div style="font-size: 0.8rem; color: #64748b;">Level</div>
            <div style="font-size: 2rem; font-weight: bold;">Lvl 3</div>
        </div>
    </div>
    <div style="background: rgba(255,255,255,0.1); border-radius: 99px; height: 10px; width: 100%; overflow: hidden;">
        <div style="background: #ffb800; width: 65%; height: 100%; box-shadow: 0 0 10px #ffb800;"></div>
    </div>
    <div style="font-size: 0.7rem; color: #64748b; margin-top: 5px; text-align: right;">350 / 500 XP to Level 4</div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)