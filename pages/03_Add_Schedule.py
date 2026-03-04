#03_Add_Schedule.py

import streamlit as st
from datetime import datetime, time, timedelta
import calendar
from database import add_schedule

# --- Helper function for Monthly repeat ---
def add_one_month(orig_date):
    """Adds exactly one month to a given date, handling edge cases like Jan 31 -> Feb 28"""
    new_month = orig_date.month + 1
    new_year = orig_date.year
    
    if new_month > 12:
        new_month = 1
        new_year += 1
        
    # Determine the maximum days in the new month (e.g., Feb has 28 or 29)
    last_day_of_month = calendar.monthrange(new_year, new_month)[1]
    
    # If original day was 31, and new month only has 30 days, adjust to 30.
    new_day = min(orig_date.day, last_day_of_month)
    
    return orig_date.replace(year=new_year, month=new_month, day=new_day)

# --- App Settings ---
st.set_page_config(page_title="Add New Schedule")

if st.button('Back to Calendar'):
    st.switch_page('01_Calendar.py')

st.title("📅 Add New Schedule")

# Input fields
title = st.text_input("Event Title")
date = st.date_input("Event Date", value=datetime.today())
is_all_day = st.checkbox("All Day")

if not is_all_day:
    col1, col2 = st.columns(2)
    with col1:
        start_time = st.time_input("Start Time", value=time(9, 0), key="start")
    with col2:
        end_time = st.time_input("End Time", value=time(10, 0), key="end")

    if end_time <= start_time:
        st.warning("End time must be later than start time.")
else:
    start_time = time(0, 0)
    end_time = time(23, 59)

# Initialize deadline to None to avoid NameError
deadline = None

repeat_option = st.selectbox(
    "Repeat",
    ("None", "Daily", "Weekly", "Biweekly", "Monthly")
)

if repeat_option != "None":
    deadline = st.date_input("Deadline", value=datetime.today())

# Save button
if st.button("Add Schedule"):
    if not title:
        st.error("⚠️ Please enter a title for your schedule.")
    
    elif not (is_all_day or end_time > start_time):
        st.error("❌ Invalid time settings. End time must be after start time.")
    
    else:
        # Case 1: Repeating Event
        if repeat_option != "None" and deadline:
            if deadline < date:
                st.error("❌ Deadline must be after the Event Date.")
            else:
                ct = 0
                match repeat_option:
                    case "Daily":
                        ct = 1
                    case "Weekly":
                        ct = 7
                    case "Biweekly":
                        ct = 14
                    case "Monthly":
                        pass 
                
                current_date = date
                
                while current_date <= deadline:
                    add_schedule(
                        title=title,
                        date=current_date.strftime('%Y-%m-%d'),
                        start_time=start_time.strftime('%H:%M'),
                        end_time=end_time.strftime('%H:%M'),
                        is_all_day=is_all_day
                    )
                    
                    # Increment the date
                    if repeat_option == "Monthly":
                        current_date = add_one_month(current_date)
                    else:
                        current_date += timedelta(days=ct)
                
                st.success(f"✅ Your schedule has been added successfully!")
                
        # Case 2: Single Event
        else:
            add_schedule(
                title=title,
                date=date.strftime('%Y-%m-%d'),
                start_time=start_time.strftime('%H:%M'),
                end_time=end_time.strftime('%H:%M'),
                is_all_day=is_all_day
            )
            st.success("✅ Your schedule has been added successfully!")