import asyncio
from os import getenv  #типо скеретный файл с токеном 
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
#from handlers import register_routes
from handlers.start import router, photo_sender     #добавила старт и просто роутер именно так он работает по другому выходит ошибка 
#from aiogram import Router, types
import os
#from handlers.start import photo_sender
from handlers.start import load_photos
from handlers.start import init_db
from handlers.start import phrase_sender   #фразочки 
from db import init_db  #из файл базы даннх 
from worker import reminder_worker    #напоминалка из фоного
from worker import prediction_worker    #предсказания из фоного 


load_dotenv()    #будет доставлять из секретного .env
TOKEN = getenv('BOT_TOKEN')

#subscribers = set()  # или твоя загрузка из файла



async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()      #регулировщик намбер 1 крутой первый
    
    init_db()    #типо база данных что ли 
    dp.include_router(router)    #диспетчер значет регулировщика втор 
    


    load_photos()       #загружает фото в память бота 
    asyncio.create_task(phrase_sender(bot))  #отправляет фразочки пользователям
    asyncio.create_task(prediction_worker(bot))   #отправляет предсказания 
    asyncio.create_task(reminder_worker(bot)) #отправляет напоминание 
    asyncio.create_task(photo_sender(bot)) # отправляет фото пользователям 
    print("Бот запущен🚀")
    await dp.start_polling(bot)   #запуск
    
    

if __name__ == '__main__':                       #запуск
    asyncio.run(main())
    
#для сервера или сайта чтоб бот не засыпал 
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive"

def run():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run).start()