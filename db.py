#база данных для напоминалки , чтоб бот запоминал 
import os
import sqlite3
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscribers (
        user_id INTEGER PRIMARY KEY
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        text TEXT,
        remind_at DATETIME
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sent_predictions (
        user_id INTEGER,
        date TEXT,
        PRIMARY KEY (user_id, date)
    )
    """)

    conn.commit()

# --- subscribers --- пользователи 

def subscribe_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO subscribers (user_id) VALUES (?)", (user_id,))
    conn.commit()

def unsubscribe_user(user_id):
    cursor.execute("DELETE FROM subscribers WHERE user_id=?", (user_id,))
    conn.commit()

def get_subscribers():
    cursor.execute("SELECT user_id FROM subscribers")
    return cursor.fetchall()

# --- reminders --- напоминание пользователю 

def add_reminder(user_id, text, remind_at):
    cursor.execute(
        "INSERT INTO reminders (user_id, text, remind_at) VALUES (?, ?, ?)",
        (user_id, text, remind_at)
    )
    conn.commit()


def get_due_reminders(now):
    cursor.execute("SELECT id, user_id, text FROM reminders WHERE remind_at <= ?", (now,))
    return cursor.fetchall()


def delete_reminder(reminder_id):
    cursor.execute("DELETE FROM reminders WHERE id=?", (reminder_id,))
    conn.commit()

# --- predictions --- предсказания 

def already_sent_today(user_id, date):
    cursor.execute(
        "SELECT 1 FROM sent_predictions WHERE user_id=? AND date=?",
        (user_id, date)
    )
    return cursor.fetchone() is not None


def mark_sent(user_id, date):
    cursor.execute(
        "INSERT OR IGNORE INTO sent_predictions (user_id, date) VALUES (?, ?)",
        (user_id, date)
    )
    conn.commit()


