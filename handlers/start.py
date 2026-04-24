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
#from db import add_reminder   #база данных
from db import subscribe_user, unsubscribe_user  #база данных
from aiogram.fsm.state import StatesGroup, State    #для игры в угадай число 
from zoneinfo import ZoneInfo   #для сервера что б он видел наш часовой пояс 




router = Router()

tz = ZoneInfo("Asia/Almaty")   #для нашего часового пояса 


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
        [KeyboardButton(text="🔮 Предсказание"), KeyboardButton(text="Угадай число")],
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
        now = datetime.now(tz)

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
        now = datetime.now(tz)

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
@router.message(lambda m: m.text == "Угадай число")
async def game_btn(message: Message, state: FSMContext):
    if await state.get_state():
        await message.answer("Ты уже в игре 😄")
        return
    


class GuessGame(StatesGroup):
    playing = State()

@router.message(Command("guess"))
async def start_guess(message: Message, state: FSMContext):
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
# 🔹 хоррор игра с сюжетом 

@router.message(Command("game"))
@router.message(F.text == "🎮 Игра")
async def start_game_handler(message: Message, state: FSMContext):
    await start_scene(message, state)

    await message.bot.send_chat_action(message.chat.id, "typing")
    await message.answer("...")

    await asyncio.sleep(1)
    await message.answer("Ты не помнишь, как сюда попал.")

    await asyncio.sleep(2)
    await message.answer("Но дверь за тобой закрылась.")

    await asyncio.sleep(2)
    await message.answer("Слишком поздно.")

    await asyncio.sleep(2)

    await start_game_handler(message, state)

    



# 🔹 Состояния
class GameState(StatesGroup):
    room = State()
    door = State()
    mirror = State()
    end = State()




# 🔹 Кнопки
room_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚪 Дверь"), KeyboardButton(text="🪞 Зеркало")],
        [KeyboardButton(text="🌑 Осмотреться"), KeyboardButton(text="🎒 Инвентарь")]
    ],
    resize_keyboard=True
)

door_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔑 Открыть"), KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

restart_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔄 Играть заново")]],
    resize_keyboard=True
)

# 🔹 Старт
@router.message(Command("game"))
async def start_scene(message: Message, state: FSMContext):
    await state.set_state(GameState.room)
    await state.update_data(
        has_key=False,
        seen_text=False,
        loop_count=0
    )

    await message.answer(
        "...\n\nТы снова просыпаешься.",
        reply_markup=room_kb
    )

# 🔹 Комната
@router.message(GameState.room)
async def room_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.text == "👀 Осмотреться":
        if not data.get("seen_text"):
            await state.update_data(seen_text=True)
            await message.answer(
                "Стены… поцарапаны.\n"
                "Будто кто-то пытался выбраться.\n\n"
                "Или ты.",
                reply_markup=room_kb
            )
        else:
            await message.answer(
                "Ты уже смотрел.\n"
                "Ничего не изменилось.\n\n"
                "Или изменилось?",
                reply_markup=room_kb
            )

    elif message.text == "🪞 Зеркало":
        await state.set_state(GameState.room)
        await message.answer(
            "Ты подходишь к зеркалу...\n\n"
            "Твоё отражение НЕ двигается.",
            reply_markup=room_kb
        )

    elif message.text == "🚪 Дверь":
        await state.set_state(GameState.door)
        await message.answer(
            "Дверь слегка приоткрыта.\n"
            "Ты уверен, что раньше она была закрыта.",
            reply_markup=door_kb
        )

    elif message.text == "🎒 Инвентарь":
        await message.answer("Пусто.\n\nНо ощущение, что что-то потерял.", reply_markup=room_kb)

# 🔹 Зеркало
@router.message(GameState.mirror)
async def mirror_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    if not data.get("has_key"):
        await state.update_data(has_key=True)
        await state.set_state(GameState.room)

        await message.answer(
            "Отражение медленно улыбается...\n"
            "И поднимает руку.\n\n"
            "В твоей руке появляется ключ 🔑",
            reply_markup=room_kb
        )
    else:
        await state.set_state(GameState.end)
        await message.answer(
            "Отражение шепчет:\n"
            "'Ты уже брал это.'\n\n"
            "Оно тянется к тебе из зеркала.\n\n💀 Концовка",
            reply_markup=restart_kb
        )

# 🔹 Дверь
@router.message(GameState.door)
async def door_handler(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.text == "🔑 Открыть":
        if not data.get("has_key"):
            await message.answer("Ты чувствуешь, что ключ был.\nНо его нет.", reply_markup=door_kb)
            return

        loop = data.get("loop_count", 0) + 1
        await state.update_data(loop_count=loop)

        if loop < 2:
            await state.set_state(GameState.room)
            await message.answer(
                "Ты открываешь дверь...\n\n"
                "И оказываешься в той же комнате.\n\n"
                "Что-то не так.",
                reply_markup=room_kb
            )
        else:
            await state.set_state(GameState.end)
            await message.answer(
                "Ты снова открываешь дверь...\n\n"
                "Но теперь там ты.\n\n"
                "Он смотрит прямо на тебя.\n\n💀 Истинная концовка",
                reply_markup=restart_kb
            )

    elif message.text == "🔙 Назад":
        await state.set_state(GameState.room)
        await message.answer("Ты отходишь...\nНо чувствуешь взгляд.", reply_markup=room_kb)

# 🔹 Рестарт
@router.message(F.text == "🔄 Играть заново")
async def restart(message: Message, state: FSMContext):
    await state.clear()
    await start_game_handler(message, state)










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
