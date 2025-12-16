import streamlit as st
from modules import ui
import pandas as pd
from modules import storage, auth, ui

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
ui.render_sidebar("Settings")
ui.load_css()

st.title("System Settings")

creds = auth.get_creds()
# Laden des aktuellen Stundenplans
schedule = storage.load_from_drive(creds, 'schedule', {})

# --- TAB 1: SCHOOL SCHEDULE ---
st.subheader("🏫 School Schedule")
st.caption("Configure your weekly timetable here. Changes apply immediately to Calendar and AI Planning.")

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
hours = [1, 2, 3, 4, 5, 6, 7, 8]

# Wir bauen einen DataFrame für den Editor
# Zeilen = Stunden (1-8), Spalten = Tage
data = []
for h in hours:
    row = {"Hour": h}
    for d in days:
        # Suche Fach für diesen Tag und Stunde
        subj = ""
        if d in schedule:
            for item in schedule[d]:
                if item['hour'] == h:
                    subj = item['subject']
        row[d] = subj
    data.append(row)

df = pd.DataFrame(data)

# Der Editor
edited_df = st.data_editor(
    df, 
    key="schedule_editor",
    use_container_width=True,
    column_config={
        "Hour": st.column_config.NumberColumn(disabled=True),
        "Monday": st.column_config.TextColumn(required=False),
        "Tuesday": st.column_config.TextColumn(required=False),
        "Wednesday": st.column_config.TextColumn(required=False),
        "Thursday": st.column_config.TextColumn(required=False),
        "Friday": st.column_config.TextColumn(required=False),
    },
    hide_index=True
)

if st.button("💾 Save Schedule", type="primary"):
    # Zurückwandeln in JSON Format für brain.py
    new_schedule = {}
    
    for index, row in edited_df.iterrows():
        hour = row['Hour']
        for day in days:
            subject = row[day]
            if subject and subject.strip() != "":
                if day not in new_schedule: new_schedule[day] = []
                new_schedule[day].append({"hour": int(hour), "subject": subject.strip()})
    
    storage.save_to_drive(creds, 'schedule', new_schedule)
    st.success("Timetable updated! Check your Calendar.")

st.divider()

# --- TAB 2: SYSTEM ---
try:
    user_id = creds.client_id[:15] + "..."
except:
    user_id = "Google User"

st.code(f"""
OS Version: Kairos 2.3 (Build 2025.12)
User: {user_id}
Timezone: Europe/Berlin
""", language="text")

if st.button("🗑️ Clear Cache"):
    st.cache_data.clear()
    st.success("Cache cleared.")