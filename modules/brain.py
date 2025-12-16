import datetime
from dateutil import parser

# Stundenplan Logik (Dynamisch)
def get_school_schedule(schedule_data, day_name):
    """
    Holt den Stundenplan für einen Wochentag aus den gespeicherten Daten.
    schedule_data: Das JSON Objekt aus storage.load('schedule')
    day_name: 'Monday', 'Tuesday', etc.
    """
    if not schedule_data:
        return [] # Leere Liste wenn keine Daten da sind
        
    return schedule_data.get(day_name, [])

def add_school_blocks(api_events, current_day, schedule_data):
    """Fügt Schulblöcke basierend auf dem gespeicherten Plan hinzu"""
    day_name = current_day.strftime("%A") # "Monday"
    school_subjects = get_school_schedule(schedule_data, day_name)
    
    school_events = []
    
    # Mapping von Stunde (1-6) zu Uhrzeiten
    # Kann man später auch dynamisch machen, hier Standard
    time_map = {
        1: ("08:00", "08:45"),
        2: ("08:50", "09:35"),
        3: ("09:55", "10:40"),
        4: ("10:45", "11:30"),
        5: ("11:45", "12:30"),
        6: ("12:35", "13:20"),
        7: ("13:30", "14:15"), # Nachmittagsunterricht
        8: ("14:15", "15:00")
    }

    for subject_info in school_subjects:
        # subject_info ist z.B. {"hour": 1, "subject": "Mathe"}
        hour_idx = int(subject_info['hour'])
        subj_name = subject_info['subject']
        
        if hour_idx in time_map:
            start_str, end_str = time_map[hour_idx]
            
            # Datum + Uhrzeit kombinieren
            start_dt = datetime.datetime.combine(current_day.date(), datetime.datetime.strptime(start_str, "%H:%M").time())
            end_dt = datetime.datetime.combine(current_day.date(), datetime.datetime.strptime(end_str, "%H:%M").time())
            
            school_events.append({
                'summary': f"🏫 {subj_name}",
                'start': {'dateTime': start_dt.isoformat()},
                'end': {'dateTime': end_dt.isoformat()},
                'is_school': True
            })
            
    return api_events + school_events

# ... (parse_time und find_free_slots bleiben gleich wie vorher) ...
def parse_time(t_str):
    return parser.parse(t_str)

def find_free_slots(mixed_events, day_date, current_now=None):
    # (Dieser Code bleibt unverändert, kopiere ihn aus der alten Datei oder lass ihn stehen)
    # Kurzfassung für den Kontext:
    sorted_events = sorted(mixed_events, key=lambda x: x['start'].get('dateTime', x['start'].get('date')))
    free_slots = []
    day_start = datetime.datetime.combine(day_date.date(), datetime.time(8, 0))
    day_end = datetime.datetime.combine(day_date.date(), datetime.time(20, 0))
    
    last_end = day_start
    
    for e in sorted_events:
        # ... (Logik wie vorher) ...
        # Um Platz zu sparen hier gekürzt, da wir nur die oberen Funktionen geändert haben.
        pass 
    return [] # Placeholder, nutze den echten Code