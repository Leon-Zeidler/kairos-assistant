import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import datetime

# Pfad Setup für .env
base_path = os.path.join(os.path.dirname(__file__), '..')
load_dotenv(os.path.join(base_path, '.env'))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def suggest_slot(user_task, free_slots_with_days, deadline_str=None, energy_level="mid"):
    """
    Sucht einen Slot basierend auf Zeit, Deadline UND Energie-Level.
    """
    
    # 1. Slots vorfiltern & formatieren
    slots_str = ""
    valid_slots_map = {}
    idx = 0
    
    for slot in free_slots_with_days:
        duration = int((slot['end'] - slot['start']).seconds / 60)
        # Wir ignorieren winzige Lücken unter 15 min
        if duration >= 15: 
            day_label = slot['start'].strftime("%A")
            start_str = slot['start'].strftime("%H:%M")
            end_str = slot['end'].strftime("%H:%M")
            iso_date = slot['start'].strftime("%Y-%m-%d")
            
            slots_str += f"ID {idx}: {day_label} ({iso_date}) | {start_str}-{end_str} ({duration} min)\n"
            valid_slots_map[idx] = slot
            idx += 1

    if not slots_str:
        return {"found": False, "reason": "Keine freien Slots im Kalender gefunden."}

    # 2. Deadline Info
    deadline_info = ""
    if deadline_str:
        deadline_info = f"DEADLINE: Die Aufgabe MUSS vor dem {deadline_str} fertig sein."

    # 3. Energie Logik
    energy_prompt = ""
    if energy_level == "high":
        energy_prompt = "PREFERENZ: Das ist eine HIGH ENERGY Aufgabe. Versuche, sie VORMITTAGS (08:00 - 12:00) zu planen, wenn der User frisch ist."
    elif energy_level == "low":
        energy_prompt = "PREFERENZ: Das ist eine LOW ENERGY Aufgabe. Plane sie lieber NACHMITTAGS (13:00 - 18:00) oder am Ende des Tages."

    # 4. Der Prompt an GPT-4o
    prompt = f"""
    You are an intelligent calendar assistant.
    
    TASK: "{user_task}"
    DEADLINE INFO: {deadline_info}
    ENERGY PREFERENCE: {'PREFER MORNING (High Energy)' if energy_level == 'high' else 'PREFER AFTERNOON (Low Energy)'}
    
    AVAILABLE SLOTS:
    {slots_str}
    
    INSTRUCTIONS:
    1. Choose the BEST slot based on deadline and energy.
    2. Output strict JSON.
    3. The "reason" field must be in ENGLISH.
    
    JSON FORMAT:
    {{
        "found": true,
        "slot_id": 12,
        "new_start_time": "YYYY-MM-DD HH:MM", 
        "new_end_time": "YYYY-MM-DD HH:MM",
        "summary": "Calendar Title",
        "reason": "Short explanation in English"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Antworte nur striktes JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        
        chosen_id = result.get('slot_id')
        if result['found'] and chosen_id in valid_slots_map:
            # Validierung: Prüfen ob Slot wirklich existiert
            return result
        else:
            return {"found": False, "reason": "KI konnte keinen passenden Slot zuordnen."}
            
    except Exception as e:
        return {"found": False, "reason": str(e)}