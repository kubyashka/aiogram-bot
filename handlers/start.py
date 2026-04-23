from aiogram import Router, F
from aiogram.filters import Command 
from aiogram.types import Message, CallbackQuery
#from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton 
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,  FSInputFile   #кнопочки 
from aiogram import Bot 
from aiogram.fsm.context import FSMContext
import aiosqlite   #база данных
import asyncio
import os
import random
from datetime import datetime, time   
from texts.phrases import PHRASES   #берет фразы из папки и вставляет в переменную
from db import add_reminder   #база данных
from db import subscribe_user, unsubscribe_user  #база данных
from aiogram.fsm.state import StatesGroup, State    #для игры в угадай число 



router = Router()


PHOTOS_PATH = "photos"      


#------------------------------------------------------------------------------------------------------
DB_NAME = 'shto.sql'  #название файла с базой данных 

async def init_db():    #функция для построения базы данных 
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS subscribers (
                user_id INTEGER PRIMARY KEY,
                        full_name TEXT,
                        username TEXT
                         )
                         ''')  #внутри базы дан, мини таблица
        await db.commit()

async def add_subscriber(user_id: int, full_name: str, username: str):    #функция для нового пользователя
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''INSERT OR REPLACE INTO subscribers (user_id, full_name, username)
            VALUES (?, ?, ?)
                    ''',
            (user_id,full_name, username)
        )
        await db.commit()


async def  remove_subscriber(user_id: int):   #брать и возвращать в коде
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            'DELETE FROM subscribers WHERE user_id = ?',
            (user_id,)
        )
        await db.commit()
        
async def get_subscribers():     #получение подписчиков 
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            'SELECT user_id, full_name, username FROM subscribers'
        )
        return await cursor.fetchall()

#----------------------------------------------------------------------------------------------------------
#кнопки и меню
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📩 Подписаться"), KeyboardButton(text="❌ Отписаться")],
        [KeyboardButton(text="🔮 Предсказание"), KeyboardButton(text="⏰ Напомнить")],
        [KeyboardButton(text="🙈 Скрыть меню"),KeyboardButton(text="🎮 Игра")]
    ],
    resize_keyboard=True
)

@router.message(Command('menu'))
@router.message(Command('start'))
async def start(message: Message):
    await message.answer("Меню открыто 👇", reply_markup=main_kb)

@router.message(lambda message: message.text == "🙈 Скрыть меню")
async def hide_menu(message: Message):
    await message.answer("Меню скрыто", reply_markup=ReplyKeyboardRemove())

# 🔹 Подписка
@router.message(Command("sign"))
async def subscribe(message: Message):
    await add_subscriber(
        message.from_user.id,
        message.from_user.full_name,
        message.from_user.username
    )
    await message.answer("Ты подписался на уведомления 👍")
    try:
        photo = get_random_photo()
        await message.answer_photo(photo)
    except Exception as e:
        await message.answer("Не удалось отправить фото 😢")
        print(e)

# Подписка
@router.message(lambda message: message.text == "📩 Подписаться")
async def subscribe_btn(message: Message):
    await add_subscriber(
        message.from_user.id,
        message.from_user.full_name,
        message.from_user.username
    )
    await message.answer("Ты подписался 👍")
    try:
        photo = get_random_photo()
        await message.answer_photo(photo)
    except Exception as e:
        await message.answer("Не удалось отправить фото 😢")
        print(e)

@router.message(lambda m: m.text == "🎮 Игра")
async def game_btn(message: Message, state: FSMContext):
    await start_game(message, state)

# ==================================================================================================================
# 📸 Рандомное фото и время 
# ========================
SEND_TIMES = [    #конкретное время отправки фоток
    time(10, 30),
    time(12, 30),
    time(13, 30),
    time(14, 30),
    time(15, 0),
    time(16, 27),
    time(17, 38),
    time(20, 0),




]

all_photos = []
unused_photos = []


def load_photos():
    global all_photos, unused_photos

    for root, dirs, files in os.walk(PHOTOS_PATH):
        for file in files:
            if file.lower().endswith((".jpg", ".png", ".jpeg")):
                all_photos.append(os.path.join(root, file))

    unused_photos = all_photos.copy()


def get_random_photo():
    global unused_photos

    if not all_photos:
        raise ValueError("Нет фото! Проверь папку photos")

    if not unused_photos:
        # когда закончились — начинаем заново
        unused_photos = all_photos.copy()

    photo_path = random.choice(unused_photos)
    unused_photos.remove(photo_path)

    return FSInputFile(photo_path)




# ========================
# 🔁 Рассылка каждые по определенному времени 
# ========================

async def photo_sender(bot: Bot):
    already_sent = set()

    while True:
        now = datetime.now()

        subscribers = await get_subscribers()

        for send_time in SEND_TIMES:
            send_datetime = now.replace(
                hour=send_time.hour,
                minute=send_time.minute,
                second=0,
                microsecond=0
            )

            if 0 <= (now - send_datetime).total_seconds() < 60 and send_time not in already_sent:
                
                

                for user_id, full_name, username in subscribers:            #цикл по отправки фото подписчик
                    try:
                        photo = get_random_photo()
                        await bot.send_photo(user_id, photo)
                    except Exception as e:
                        print("Ошибка:", e)

                already_sent.add(send_time)

        if now.hour == 0 and now.minute == 0:
            already_sent.clear()

        await asyncio.sleep(10)   #проверяется время каждые 10 секунд
#===================================================================================================================

#---------рассылка фразочек-------------- 

PHRASE_TIMES = [
    time(10, 0),
    time(13, 0),
    time(14, 0),
    time(19, 0),
    time(21, 0),

]
def get_random_phrase():
    return random.choice(PHRASES)

async def phrase_sender(bot: Bot):
    already_sent = set()

    while True:
        now = datetime.now()

        subscribers = await get_subscribers()

        for send_time in PHRASE_TIMES:
            send_datetime = now.replace(
                hour=send_time.hour,
                minute=send_time.minute,
                second=0,
                microsecond=0
            )

            if 0 <= (now - send_datetime).total_seconds() < 60 and send_time not in already_sent:

                print("Отправка фразы!")

                phrase = get_random_phrase()

                for user_id, full_name, username in subscribers:
                    try:
                        await bot.send_message(user_id, phrase)
                    except Exception as e:
                        print("Ошибка:", e)

                already_sent.add(send_time)

        if now.hour == 0 and now.minute == 0:
            already_sent.clear()

        await asyncio.sleep(10)







# 🔹 Отписка
@router.message(Command("unplug"))
async def unsubscribe(message: Message):
    await remove_subscriber(message.from_user.id)
    await message.answer("Ты отписался ❌")
# Отписка
@router.message(lambda message: message.text == "❌ Отписаться")
async def unsubscribe_btn(message: Message):
    await remove_subscriber(message.from_user.id)
    await message.answer("Ты отписался ❌")

#==================================================================================================
# 🔹предсказания 

@router.message(lambda message: message.text == "🔮 Предсказание")
async def get_prediction(message: Message):
    prediction = "Сегодня тебя ждёт приятный сюрприз ✨"
    await message.answer(prediction)



@router.message(Command("predictions"))
async def start(message: Message):
    subscribe_user(message.from_user.id)
    await message.answer("Ты подписан на ежедневные предсказания 🔮")

#================================================================================================

#---------------------
#игра в угадай число
#----------------------------------------

class GuessGame(StatesGroup):
    playing = State()

@router.message(Command("game"))
async def start_game(message: Message, state: FSMContext):
    number = random.randint(1, 100)

    await state.update_data(secret_number=number)
    await state.set_state(GuessGame.playing)

    await message.answer("🎮 Я загадал число от 1 до 100\nПопробуй угадать!")

@router.message(GuessGame.playing)
async def process_guess(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введи число 😅")
        return

    guess = int(message.text)

    data = await state.get_data()
    secret = data["secret_number"]

    if guess < secret:
        await message.answer("🔼 Больше")
    elif guess > secret:
        await message.answer("🔽 Меньше")
    else:
        await message.answer("🎉 Угадал! Ты молодец💪")
        await state.clear()

@router.message(lambda m: m.text.lower() == "стоп")
async def stop_game(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Игра остановлена ❌")







#==================================================================================================
# 🔹 Напоминание 

from aiogram.fsm.state import StatesGroup, State

class ReminderState(StatesGroup):
    date = State()
    time = State()
    text = State()
@router.message(Command("remind"))
async def start_reminder(message: Message, state: FSMContext):
    await message.answer("Введи дату (пример: 04.05.2002)")    #выбор даты 
    await state.set_state(ReminderState.date)



@router.message(lambda msg: msg.text == "⏰ Напомнить")    #старт комнды напоминания 
async def start_reminder(message: Message, state: FSMContext):
    await message.answer("Введи дату (пример: 04.05.2002)")    #выбор даты 
    await state.set_state(ReminderState.date)

@router.message(ReminderState.date)
async def get_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    await message.answer("Теперь время (пример: 18:30)")   #выбор вренени 
    await state.set_state(ReminderState.time)

@router.message(ReminderState.time)
async def get_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    await message.answer("Что напомнить?")
    await state.set_state(ReminderState.text)

@router.message(ReminderState.text)
async def save_reminder(message: Message, state: FSMContext):
    data = await state.get_data()

    try:
        remind_at = datetime.strptime(
            f"{data['date']} {data['time']}",
            "%d.%m.%Y %H:%M"
        )
    except:
        await message.answer("Ошибка формата 😢 Попробуй заново")
        return

    add_reminder(
        user_id=message.from_user.id,
        text=message.text,
        remind_at=remind_at
    )

    await message.answer("Напоминание сохранено ✅")
    await state.clear()

from db import get_due_reminders, delete_reminder













#__________________________________________________________________________________________________    
@router.message(Command('secret_users'))   #список пользователей, это для себя 
async def users(message: Message):
    users = await get_subscribers()

    text = 'Пользователи в базе:\n\n'
    for user_id, full_name, username in users:
        if username:
            text += f' {full_name} (@{username})\n'
        else:
            text += f' {full_name}\n'
                    
                    
    await message.answer(text)
#__________________________________________________________________________________________________

