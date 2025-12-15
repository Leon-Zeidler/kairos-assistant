from datetime import datetime, timedelta

def parse_time(iso_input):
    if isinstance(iso_input, datetime): return iso_input
    
    # 1. Zuerst das 'Z' (UTC Markierung) entfernen, falls vorhanden
    clean = iso_input.replace('Z', '')
    
    # 2. Zeitzone (+01:00) abschneiden
    clean = clean.split('+')[0]
    
    # 3. WICHTIG: Millisekunden (.141228) abschneiden <-- Das fixt deinen Fehler!
    clean = clean.split('.')[0]
    
    if 'T' in clean:
        return datetime.strptime(clean, "%Y-%m-%dT%H:%M:%S")
    else:
        return datetime.strptime(clean, "%Y-%m-%d")

def add_school_blocks(events, search_date, weekly_schedule):
    events_copy = events.copy()
    weekday = search_date.weekday()
    day_config = weekly_schedule.get(str(weekday)) or weekly_schedule.get(weekday)

    if day_config and day_config.get('active'):
        s_h, e_h = day_config['start'], day_config['end']
        if e_h > s_h:
            s_dt = search_date.replace(hour=s_h, minute=0, second=0)
            e_dt = search_date.replace(hour=e_h, minute=0, second=0)
            events_copy.append({
                'summary': '🏫 Schule',
                'start': {'dateTime': s_dt.isoformat()},
                'end': {'dateTime': e_dt.isoformat()},
                'is_fake': True
            })
            events_copy.sort(key=lambda x: x['start'].get('dateTime', ''))
    return events_copy

def find_free_slots(events, search_date, current_now=None):
    """
    Berechnet freie Slots.
    current_now: Die aktuelle echte Uhrzeit (um Vergangenheit abzuschneiden).
    """
    # Standard: Tag geht von 06:00 bis 22:00
    day_start = search_date.replace(hour=6, minute=0, second=0)
    day_end = search_date.replace(hour=22, minute=0, second=0)
    
    # ZEIT-CHECK: Wenn wir HEUTE anschauen, dürfen wir nicht in der Vergangenheit planen
    if current_now and search_date.date() == current_now.date():
        # Wir starten erst ab "Jetzt + 15 Min Puffer"
        start_buffer = current_now + timedelta(minutes=15)
        # Wenn es schon spät ist (z.B. 23 Uhr), ist der Start nach dem Ende -> Keine Slots
        if start_buffer > day_end:
            return []
        # Wenn Jetzt (z.B. 14:00) nach 06:00 ist, schieben wir den Start nach hinten
        if start_buffer > day_start:
            day_start = start_buffer.replace(second=0, microsecond=0)

    free_slots = [{'start': day_start, 'end': day_end}]

    for event in events:
        s_raw = event['start'].get('dateTime')
        if not s_raw: continue 
        ev_start = parse_time(s_raw)
        ev_end = parse_time(event['end'].get('dateTime'))

        new_free_slots = []
        for slot in free_slots:
            # Keine Überschneidung
            if ev_end <= slot['start'] or ev_start >= slot['end']:
                new_free_slots.append(slot)
            else:
                # Überschneidung -> Slot teilen
                if slot['start'] < ev_start:
                    new_free_slots.append({'start': slot['start'], 'end': ev_start})
                if slot['end'] > ev_end:
                    new_free_slots.append({'start': ev_end, 'end': slot['end']})
        free_slots = new_free_slots

    return free_slots