#01_Calendar.py

import streamlit as st
import streamlit_calendar as st_calendar
import os
import sqlite3
from datetime import datetime
from google import genai
from database import init_db, update_schedule_datetime
from dotenv import load_dotenv

DB_NAME = "./schedule_app.db" 
st.set_page_config(page_title="My Schedule")
load_dotenv()
init_db()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("Gemini API key is not set.")
    st.stop()

client = genai.Client(api_key=GEMINI_API_KEY)

# --- Database Operations ---
def get_events_from_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, start_time, end_time, is_all_day FROM schedules")
    rows = cursor.fetchall()
    conn.close()

    event_list = []
    for row in rows:
        event = {}
        event['id'] = row[0]
        event['title'] = row[1]
        start_time_str = row[2] 
        end_time_str = row[3]   
        is_all_day = row[4]     

        if is_all_day:
            event['start'] = start_time_str.split(' ')[0]
            event['end'] = end_time_str.split(' ')[0]
            event['allDay'] = True
        else:
            start_dt = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
            end_dt = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M')
            event['start'] = start_dt.isoformat()
            event['end'] = end_dt.isoformat()
            event['allDay'] = False

        event['editable'] = True 
        event_list.append(event)

    return event_list

def delete_event_from_db(event_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM schedules WHERE id = ?", (event_id,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        st.error(f"Database Error: {e}")
        return False

def delete_future_events_from_db(title, start_time_str):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM schedules WHERE title = ? AND start_time >= ?", (title, start_time_str))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        st.error(f"Database Error: {e}")
        return False

def generate_schedule_advice(events: list) -> str:
    if not events:
        return "There are currently no events registered. Let's add a new schedule!"

    event_descriptions = []
    for event in events:
        title = event.get('title', 'Unknown Event')
        start = event.get('start', 'Unknown Start Time')
        end = event.get('end', 'Unknown End Time')
        all_day = event.get('allDay', False)

        if all_day:
            event_descriptions.append(f"- All-day event: {title} ({start})")
        else:
            event_descriptions.append(f"- Event: {title} (From {start} to {end})")

    prompt = f"""
            Based on the following list of schedules and tasks, please generate specific advice
            for effective time management, productivity improvement, or stress reduction.

            Current Schedule:
            {chr(10).join(event_descriptions)}

            Advice:
            """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"An error occurred while generating advice: {e}"

# --- Initialize Session States ---
if 'advice_text' not in st.session_state:
    st.session_state.advice_text = ""
if 'calendar_date' not in st.session_state:
    st.session_state.calendar_date = datetime.today().strftime('%Y-%m-%d')
if 'calendar_view' not in st.session_state:
    st.session_state.calendar_view = 'dayGridMonth'
if 'last_processed_drag' not in st.session_state:
    st.session_state.last_processed_drag = None

# ==========================================
# 🌟 MAGIC TRICK: Process Drag & Drop BEFORE fetching DB
# ==========================================
# By catching the event from session_state before the page loads, 
# we prevent the annoying "snap-back" glitch without needing a double reload.
if "my_calendar" in st.session_state and st.session_state.my_calendar:
    cal_data = st.session_state.my_calendar
    if "eventChange" in cal_data:
        event_info = cal_data["eventChange"]["event"]
        
        # Create a unique signature to avoid processing the same drag twice
        change_sig = f"{event_info['id']}_{event_info['start']}_{event_info['end']}"
        
        if st.session_state.last_processed_drag != change_sig:
            new_start_dt = datetime.fromisoformat(event_info['start'])
            new_end_dt = datetime.fromisoformat(event_info['end'])
            db_start_str = new_start_dt.strftime('%Y-%m-%d %H:%M')
            db_end_str = new_end_dt.strftime('%Y-%m-%d %H:%M')
            
            try:
                # Update DB silently
                update_schedule_datetime(event_id=event_info['id'], new_start=db_start_str, new_end=db_end_str)
                st.session_state.last_processed_drag = change_sig
                
                # Remember the current view
                st.session_state.calendar_date = event_info['start'].split('T')[0]
                if 'view' in cal_data['eventChange']:
                    st.session_state.calendar_view = cal_data['eventChange']['view']['type']
            except Exception as e:
                st.error(f"Error updating database: {e}")

# --- Load Events (Now containing the updated times!) ---
if os.path.exists(DB_NAME):
    event_list = get_events_from_db()
else:
    event_list = []

st.header('📅 My Calendar')
st.subheader('🤖 Schedule Planning Advice')

if st.button('Get Advice'):
    with st.spinner('Generating advice...'):
        st.session_state.advice_text = generate_schedule_advice(event_list)

if st.session_state.advice_text:
    st.write(st.session_state.advice_text)

col1, col2 = st.columns(2)
with col1:
    if st.button('Add Schedule'):
        st.session_state.advice_text = ""
        st.switch_page('pages/03_Add_Schedule.py')
with col2:
    if st.button('To-Do List'):
        st.session_state.advice_text = ""
        st.switch_page('pages/02_To_Do_List.py')

# --- Calendar Settings ---
options = {
    'initialView': st.session_state.calendar_view, 
    'initialDate': st.session_state.calendar_date, 
    'headerToolbar': {
        'left': 'today prev,next',
        'center': 'title',
        'right': 'dayGridMonth,timeGridWeek,timeGridDay',
    },
    'titleFormat': {
        'year': 'numeric', 'month': 'long'
    },
    'buttonText': {
        'today': 'Today',
        'month': 'Month',
        'week': 'Week',
        'day': 'Day',
        'list': 'List'
    },
    'locale': 'en', 
    'firstDay': '0', 
    'navLinks': True,
    'selectable': True,
    'editable': True,
}

# Added key="my_calendar" to link it to the session_state logic above
calendar = st_calendar.calendar(events = event_list, options = options, key="my_calendar")

# --- Click Event for Deletion ---
if calendar and 'eventClick' in calendar:
    clicked_event_info = calendar['eventClick']['event']
    event_id = int(clicked_event_info['id'])
    event_title = clicked_event_info['title']
    
    st.session_state.calendar_date = clicked_event_info['start'].split('T')[0]
    if 'view' in calendar['eventClick']:
        st.session_state.calendar_view = calendar['eventClick']['view']['type']
    
    if clicked_event_info['allDay']:
        start_date = datetime.fromisoformat(clicked_event_info['start'].split('T')[0]).strftime('%b %d, %Y')
        end_date = start_date
        time_str = "All-day"
        db_compare_time = datetime.fromisoformat(clicked_event_info['start'].split('T')[0]).strftime('%Y-%m-%d 00:00')
    else:
        start_dt = datetime.fromisoformat(clicked_event_info['start'])
        end_dt = datetime.fromisoformat(clicked_event_info['end'])
        start_date = start_dt.strftime('%b %d, %Y')
        end_date = end_dt.strftime('%b %d, %Y')
        time_str = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
        db_compare_time = start_dt.strftime('%Y-%m-%d %H:%M')

    with st.expander(f"[Event Details] {event_title}", expanded=True):
        st.write(f"**Date & Time:** {start_date} | {time_str}")
        
        col_del1, col_del2 = st.columns(2)
        
        with col_del1:
            if st.button("Delete ONLY this event", key=f"del_one_{event_id}"):
                if delete_event_from_db(event_id):
                    st.success("Deleted.")
                    st.session_state.advice_text = ""
                    st.rerun() 
                    
        with col_del2:
            if st.button("Delete this & FUTURE events", key=f"del_future_{event_id}"):
                if delete_future_events_from_db(event_title, db_compare_time):
                    st.success("Deleted this and future events.")
                    st.session_state.advice_text = ""
                    st.rerun()