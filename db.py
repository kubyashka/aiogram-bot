#база данных для напоминалки , чтоб бот запоминал 
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# ---------------- INIT DB ----------------
def init_db():
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            user_id BIGINT PRIMARY KEY
        )
    """)


    cur.execute("""
        CREATE TABLE IF NOT EXISTS sent_predictions (
            user_id BIGINT,
            date TEXT,
            PRIMARY KEY (user_id, date)
        )
    """)

    conn.commit()

# ---------------- SUBSCRIBERS ----------------
def subscribe_user(user_id):
    cur.execute("""
        INSERT INTO subscribers (user_id)
        VALUES (%s)
        ON CONFLICT DO NOTHING
    """, (user_id,))
    conn.commit()

def unsubscribe_user(user_id):
    cur.execute("""
        DELETE FROM subscribers WHERE user_id = %s
    """, (user_id,))
    conn.commit()

def get_subscribers():
    cur.execute("SELECT user_id FROM subscribers")
    return [row[0] for row in cur.fetchall()]



# ---------------- PREDICTIONS ----------------
def already_sent_today(user_id, date):
    cur.execute("""
        SELECT 1 FROM sent_predictions
        WHERE user_id = %s AND date = %s
    """, (user_id, date))
    return cur.fetchone() is not None

def mark_sent(user_id, date):
    cur.execute("""
        INSERT INTO sent_predictions (user_id, date)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
    """, (user_id, date))
    conn.commit()