# database.py

import sqlite3
import pandas as pd

DB_NAME = "schedule_app.db"


# -------------------------
# Initialize Database
# -------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tasks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        deadline TEXT,
        status TEXT DEFAULT 'Not Started',
        priority TEXT DEFAULT 'Medium',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Schedules table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        title TEXT NOT NULL,
        start_time TEXT,
        end_time TEXT,
        is_all_day BOOLEAN,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks(id)
    )
    """)

    conn.commit()
    conn.close()


# -------------------------
# Task Functions
# -------------------------
def load_all_tasks() -> pd.DataFrame:
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM tasks", conn, index_col="id")
    
    if "deadline" in df.columns:
        df["deadline"] = pd.to_datetime(df["deadline"], errors="coerce")

    conn.close()
    return df


def save_all_tasks(df: pd.DataFrame):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks")

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO tasks (title, deadline, status, priority)
            VALUES (?, ?, ?, ?)
        """, (
            row["title"],
            row["deadline"],
            row["status"],
            row["priority"]
        ))

    conn.commit()
    conn.close()


def add_task(title, deadline=None, status="Not Started", priority="Medium"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tasks (title, deadline, status, priority)
        VALUES (?, ?, ?, ?)
    """, (title, deadline, status, priority))

    conn.commit()
    conn.close()


# -------------------------
# Schedule Functions
# -------------------------
def add_schedule(title, date, start_time, end_time, is_all_day, task_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    start_time_str = f"{date} {start_time}"
    end_time_str = f"{date} {end_time}"

    cursor.execute("""
        INSERT INTO schedules (task_id, title, start_time, end_time, is_all_day)
        VALUES (?, ?, ?, ?, ?)
    """, (task_id, title, start_time_str, end_time_str, is_all_day))

    conn.commit()
    conn.close()


def update_schedule_datetime(event_id, new_start, new_end):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE schedules
        SET start_time = ?, end_time = ?
        WHERE id = ?
    """, (new_start, new_end, event_id))

    conn.commit()
    conn.close()


def get_all_tasks():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, deadline, status, priority
        FROM tasks
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows