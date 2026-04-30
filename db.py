#база данных для напоминалки , чтоб бот запоминал 
import os
import aiosqlite

DB_NAME = "bot.db"


# ---------------- INIT DB ----------------
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                user_id INTEGER PRIMARY KEY
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS sent_predictions (
                user_id INTEGER,
                date TEXT,
                PRIMARY KEY (user_id, date)
            )
        """)

        await db.commit()


# ---------------- SUBSCRIBERS ----------------
async def subscribe_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR IGNORE INTO subscribers (user_id)
            VALUES (?)
        """, (user_id,))
        await db.commit()


async def unsubscribe_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            DELETE FROM subscribers WHERE user_id = ?
        """, (user_id,))
        await db.commit()


async def get_subscribers():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM subscribers")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


# ---------------- PREDICTIONS ----------------
async def already_sent_today(user_id: int, date: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT 1 FROM sent_predictions
            WHERE user_id = ? AND date = ?
        """, (user_id, date))

        return await cursor.fetchone() is not None


async def mark_sent(user_id: int, date: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR IGNORE INTO sent_predictions (user_id, date)
            VALUES (?, ?)
        """, (user_id, date))
        await db.commit()
