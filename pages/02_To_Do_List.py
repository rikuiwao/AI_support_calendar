#02_To_Do_List.py

import streamlit as st
from database import load_all_tasks, save_all_tasks, add_schedule
from streamlit.column_config import TextColumn, DateColumn, SelectboxColumn, NumberColumn
from datetime import date, datetime
import sqlite3
import pandas as pd
import json
import os
from google import genai
from dotenv import load_dotenv

# --- Setup Gemini API ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
DB_NAME = "./schedule_app.db"

st.set_page_config(page_title="To-Do List & Auto-Schedule")

if st.button('Back to Calendar'):
    st.switch_page('01_Calendar.py')

# --- Helper Functions ---
def get_busy_slots_text():
    """Fetch current schedules from DB to send to Gemini"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT title, start_time, end_time FROM schedules WHERE is_all_day = 0")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return "No existing schedules. The calendar is completely free."
    busy_text = ""
    for row in rows:
        busy_text += f"- {row[0]}: From {row[1]} to {row[2]}\n"
    return busy_text

def delete_future_events_from_db(title):
    """Delete all events with the specified title from the calendar"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM schedules WHERE title = ?", (title,))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        st.error(f"Database Error: {e}")

# ==========================================
# 1. AI Task Input Form
# ==========================================
st.header("✨ Add Task & AI Auto-Schedule")
st.write("Enter your task details and constraints, and the AI will schedule it for you.")

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        task_title = st.text_input("Task Title (e.g., TOEIC Study)")
        estimated_hours = st.number_input("Total Needed Hours", min_value=0.5, step=0.5, value=5.0)
    with col2:
        deadline = st.date_input("Deadline", value=datetime.today())
        priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)

    # Optional Constraints
    st.write("**Advanced Constraints (Optional)**")
    col_opt1, col_opt2 = st.columns(2)
    
    with col_opt1:
        # Session length preference
        session_length = st.slider("Hours per session", 0.5, 3.0, (1.0, 2.0), step=0.5)
        
        use_days = st.checkbox("Specify Days of the Week")
        allowed_days = []
        if use_days:
            allowed_days = st.multiselect(
                "Select allowed days:",
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            )
            
    with col_opt2:
        # Max frequency per week
        max_days_per_week = st.number_input("Max sessions per week", min_value=1, max_value=7, value=5)
        
        use_time = st.checkbox("Specify Time Blocks")
        allowed_times = []
        if use_time:
            allowed_times = st.multiselect(
                "Select allowed time blocks:",
                [
                    "12 a.m. - 3 a.m.",   # 00:00 - 03:00
                    "3 a.m. - 6 a.m.",    # 03:00 - 06:00
                    "6 a.m. - 9 a.m.",    # 06:00 - 09:00
                    "9 a.m. - 12 p.m.",   # 09:00 - 12:00
                    "12 p.m. - 3 p.m.",   # 12:00 - 15:00
                    "3 p.m. - 6 p.m.",    # 15:00 - 18:00
                    "6 p.m. - 9 p.m.",    # 18:00 - 21:00
                    "9 p.m. - 11:59 p.m." # 21:00 - 23:59
                ]
            )

    # Schedule generation button
    if st.button("🚀 Schedule with AI", type="primary"):
        if not task_title:
            st.error("⚠️ Please enter a Task Title.")
        elif use_days and not allowed_days:
            st.error("⚠️ Please select at least one day.")
        elif use_time and not allowed_times:
            st.error("⚠️ Please select at least one time block.")
        elif not client:
            st.error("⚠️ Gemini API Key is missing.")
        else:
            with st.spinner(f"AI is calculating the best time slots for '{task_title}'..."):
                busy_slots = get_busy_slots_text()
                today_str = datetime.today().strftime('%Y-%m-%d')
                
                days_constraint = f"You MUST ONLY schedule on these days of the week: {', '.join(allowed_days)}." if use_days else "You can schedule on any day of the week."
                time_constraint = f"You MUST ONLY schedule within these time blocks: {', '.join(allowed_times)}." if use_time else "You can schedule at any reasonable time between 08:00 and 22:00."
                
                # Prompt with strong human-like behavior instructions
                prompt = f"""
                You are a professional AI scheduling assistant.
                Task: "{task_title}"
                Total Hours Needed: {estimated_hours}
                Deadline: {deadline.strftime('%Y-%m-%d')}
                Today's date: {today_str}. Do NOT schedule anything in the past.

                Constraints:
                - Length per session: Between {session_length[0]} and {session_length[1]} hours.
                - Frequency: Maximum {max_days_per_week} sessions per week.
                - {days_constraint}
                - {time_constraint}

                Currently booked times (DO NOT OVERLAP with these):
                {busy_slots}

                CRITICAL BEHAVIORAL INSTRUCTIONS:
                1. DO NOT schedule the task at the exact same time every day. 
                2. Vary the start times naturally (e.g., morning one day, afternoon another).
                3. Skip days if necessary to meet the "sessions per week" constraint.
                4. The user selected constraints in 12-hour AM/PM format, but you MUST output the times in 24-hour format (HH:MM, e.g., 14:00).
                5. NEVER use "24:00". If an event ends at midnight, use "23:59" instead.
                6. Output ONLY a valid JSON array of objects. No markdown.
                
                Format:
                [
                    {{"date": "YYYY-MM-DD", "start_time": "HH:MM", "end_time": "HH:MM"}}
                ]
                """
                
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                    )
                    
                    raw_text = response.text.strip()
                    if raw_text.startswith("```json"):
                        raw_text = raw_text[7:-3].strip()
                    elif raw_text.startswith("```"):
                        raw_text = raw_text[3:-3].strip()
                        
                    schedule_data = json.loads(raw_text)
                    
                    # 1. Save to Calendar (schedules table)
                    count = 0
                    for item in schedule_data:
                        add_schedule(
                            title=task_title,
                            date=item['date'],
                            start_time=item['start_time'],
                            end_time=item['end_time'],
                            is_all_day=False
                        )
                        count += 1
                    
                    # 2. Save to To-Do List (tasks table)
                    tasks_df = load_all_tasks()
                    new_task = pd.DataFrame([{
                        "title": task_title,
                        "deadline": deadline.strftime('%Y-%m-%d'),
                        "estimated_hours": estimated_hours,
                        "status": "Not Started",
                        "priority": priority
                    }])
                    updated_df = pd.concat([tasks_df, new_task], ignore_index=True)
                    
                    # [CRITICAL FIX] Force the entire 'deadline' column to be standard strings to prevent Timestamp error!
                    updated_df['deadline'] = pd.to_datetime(updated_df['deadline']).dt.strftime('%Y-%m-%d')
                    
                    save_all_tasks(updated_df)
                        
                    st.success(f"✅ AI successfully scheduled {count} sessions! Task added to the list below.")
                    
                except json.JSONDecodeError:
                    st.error("❌ Failed to parse AI response. Please try again.")
                except Exception as e:
                    st.error(f"❌ An error occurred: {e}")

st.divider()

# ==========================================
# 2. Task List Table
# ==========================================
st.header("📝 Task List (Edit & Delete)")
st.info("If you mark a task as 'Completed' and save, it will be removed, and its future calendar events will also be deleted.")

with st.form(key="unified_form"):
    tasks_df = load_all_tasks()
    
    if 'estimated_hours' not in tasks_df.columns:
        tasks_df['estimated_hours'] = 0.0

    tasks_df_no_index = tasks_df.reset_index()

    edited_df_no_index = st.data_editor(
        tasks_df_no_index,
        column_config={
            "id": None, 
            "title": TextColumn("Task Title", required=True, width="large"),
            "deadline": DateColumn("Deadline", format="YYYY/MM/DD"),
            "estimated_hours": NumberColumn("Hours", min_value=0.0, step=0.5, format="%.1f h", disabled=True), 
            "status": SelectboxColumn("Status", options=["Not Started", "In Progress", "Completed"], required=True),
            "priority": SelectboxColumn("Priority", options=["High", "Medium", "Low"], required=True),
        },
        use_container_width=True,
        num_rows="dynamic",
        key="editor",
        hide_index=True
    )
    
    submitted = st.form_submit_button("Save Changes")

if submitted:
    # Detect deleted (or Completed) tasks and remove them from the calendar
    original_titles = set(tasks_df['title'].tolist())
    
    edited_df_no_index['deadline'] = pd.to_datetime(edited_df_no_index['deadline']).dt.strftime('%Y-%m-%d')
    
    final_df = edited_df_no_index[edited_df_no_index['status'] != 'Completed'].copy()
    remaining_titles = set(final_df['title'].tolist())
    
    deleted_titles = original_titles - remaining_titles
    for deleted_title in deleted_titles:
        delete_future_events_from_db(deleted_title) 

    if 'id' in final_df.columns:
        final_df = final_df.set_index('id')
    
    save_all_tasks(final_df)
    st.toast("✅ Changes saved and calendar updated!")
    st.rerun()