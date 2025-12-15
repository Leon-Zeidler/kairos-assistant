import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import datetime

# --- WICHTIG: Hier startet die Verbindung ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def suggest_slot(user_task, free_slots_with_days, deadline_str=None):
    """
    Sucht einen Slot für eine Aufgabe.
    deadline_str: "YYYY-MM-DD" oder None
    """
    
    slots_str = ""
    valid_slots_map = {}

    idx = 0
    for slot in free_slots_with_days:
        duration = int((slot['end'] - slot['start']).seconds / 60)
        if duration >= 15: 
            day_label = slot['start'].strftime("%A %d.%m.")
            iso_date = slot['start'].strftime("%Y-%m-%d")
            
            start_str = slot['start'].strftime("%H:%M")
            end_str = slot['end'].strftime("%H:%M")
            
            slots_str += f"ID {idx}: [{day_label}] ({iso_date}) {start_str}-{end_str} ({duration} min)\n"
            valid_slots_map[idx] = slot
            idx += 1

    if not slots_str:
        return {"found": False, "reason": "Keine freien Slots gefunden."}

    # DEADLINE LOGIK IM PROMPT
    deadline_info = ""
    if deadline_str:
        deadline_info = f"WICHTIG: Die Aufgabe MUSS vor dem {deadline_str} erledigt sein! Ignoriere alle Slots, die nach diesem Datum liegen."

    prompt = f"""
    Du bist Kairos, ein intelligenter Wochenplaner.
    
    TASK: "{user_task}"
    {deadline_info}
    
    HIER SIND DIE FREIEN SLOTS:
    {slots_str}
    
    AUFGABE:
    1. Suche den BESTEN Slot. 
    2. Wenn eine Deadline existiert, wähle einen Slot DAVOR.
    3. Wenn die Deadline morgen ist, plane es HEUTE oder MORGEN früh.
    
    Antworte JSON:
    {{
        "found": true,
        "slot_id": 12,
        "new_start_time": "YYYY-MM-DD HH:MM", 
        "new_end_time": "YYYY-MM-DD HH:MM",
        "summary": "Titel",
        "reason": "Erklärung (z.B. passt vor Deadline)"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Antworte nur JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        
        chosen_id = result.get('slot_id')
        if result['found'] and chosen_id in valid_slots_map:
            return result
        else:
            return {"found": False, "reason": "KI hat ungültige ID gewählt oder Deadline nicht haltbar."}
            
    except Exception as e:
        return {"found": False, "reason": str(e)}