import streamlit as st
import pandas as pd
from modules import storage, auth

st.set_page_config(page_title="Analytics", page_icon="📊")

creds = auth.get_creds()
tasks = storage.load_from_drive(creds, 'tasks', [])

st.title("📊 System Analytics")

if not tasks:
    st.info("Keine Daten für Analyse verfügbar.")
else:
    # Daten vorbereiten
    df = pd.DataFrame(tasks)
    
    # 1. Verteilung nach Kategorie
    st.subheader("Workload nach Kategorie")
    if 'category' in df.columns:
        cat_counts = df['category'].value_counts()
        st.bar_chart(cat_counts)
    
    # 2. Verteilung nach Energie
    st.subheader("Energie Bedarf")
    if 'energy' in df.columns:
        energy_counts = df['energy'].value_counts()
        st.bar_chart(energy_counts, color="#ffaa00")

    # 3. Quick Stats
    total_mins = df['duration'].sum()
    hours = total_mins // 60
    mins = total_mins % 60
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Tasks im Backlog", len(tasks))
    c2.metric("Zeit Investition", f"{hours}h {mins}m")
    c3.metric("Durchschnittsdauer", f"{int(df['duration'].mean())} min")