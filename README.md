# 📅 AI-Powered Schedule & To-Do Manager
![Main View](https://github.com/user-attachments/assets/f60bb652-a3f6-401f-98e7-3becb85ee0da)

An intelligent calendar and task management application built with Python and Streamlit. This app seamlessly integrates a traditional to-do list with a dynamic calendar, leveraging Google's Gemini AI to automatically schedule your tasks based on estimated hours, deadlines, and your personal time constraints.

## ✨ Key Features

- **Interactive Calendar**: View your schedule in Month, Week, or Day formats. Supports drag-and-drop to easily adjust events on the fly.
- **Smart To-Do List**: Manage your tasks with statuses (Not Started, In Progress, Completed), deadlines, and priorities.
- **🤖 AI Auto-Scheduling**: 
  - Input a task, estimated completion hours, and deadline.
  - Set specific constraints (e.g., "Only Mondays and Wednesdays", "Between 6 p.m. - 9 p.m.", "Max 3 days a week").
  - The AI (powered by Gemini 2.5 Flash) will analyze your existing calendar, find empty slots, and automatically divide and assign the task into reasonable sessions.
- **Auto-Sync**: Marking a task as "Completed" or deleting it from the To-Do list will automatically clean up all associated future events from your calendar.
- **AI Planning Advice**: Get AI-generated tips for time management and productivity based on your current schedule.

## 🛠️ Tech Stack

- **Frontend/Framework**: [Streamlit](https://streamlit.io/)
- **Calendar UI**: `streamlit-calendar` (FullCalendar integration)
- **Database**: SQLite3
- **Data Manipulation**: Pandas
- **AI Engine**: Google GenAI (`gemini-2.5-flash`)

## 📂 Project Structure

```text
├── .env                    # Environment variables (API Key)
├── requirements.txt        # Python dependencies
├── database.py             # SQLite database initialization and queries
├── 01_Calendar.py          # Main application entry point & Calendar View
└── pages/
    ├── 02_To_Do_List.py    # To-Do List & AI Auto-Scheduling logic
    └── 03_Add_Schedule.py  # Manual schedule entry
```
## 🚀 Getting Started
1. **Prerequisites**:　　
Ensure you have Python 3.8+ installed. You also need a Google Gemini API key.
2. **Installation**:　　
Clone the repository and install the required dependencies:
```text
git clone https://github.com/rikuiwao/AI_support_calendar
cd <your-project-folder>
pip install -r requirements.txt
```
3. **Environment Setup**:  
Create a .env file in the root directory and add your Gemini API key:
```text
GEMINI_API_KEY=your_actual_api_key_here
```
4. **Run the Application**:  
Start the Streamlit server by running the main calendar file:
```text
streamlit run 01_Calendar.py
```

## 💡 Usage Guide
1. **Adding Manual Events**:
Go to the "Add Schedule" page to block out times for meetings or personal events.

2. **AI Task Scheduling**:
Navigate to the "To-Do List" page. Enter a new task in the top panel, set your time constraints, and click "🚀 Schedule with AI". The AI will populate your calendar.

3. **Task Management**:
Update task statuses directly in the To-Do list table. Click "Save Changes" to reflect updates on your calendar.

## ⚠️ Important Notes
- The SQLite database (schedule_app.db) is automatically generated upon the first run.
- If you encounter database schema errors during development, simply delete the schedule_app.db file and restart the app to rebuild the tables.
