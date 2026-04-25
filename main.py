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
#from handlers.start import init_db
from handlers.start import phrase_sender   #фразочки 
from db import init_db  #из файл базы даннх 
from worker import prediction_worker    #предсказания из фоного 
from fastapi import FastAPI  #что б сервер не засыпал
import threading   #чтоб сервер не засыпал
import uvicorn    #чтоб сервер не засыпал




load_dotenv()    #будет доставлять из секретного .env
TOKEN = getenv('BOT_TOKEN')



app = FastAPI()         #для сервера или сайта чтоб бот не засыпал 

@app.get("/")           #для сервера или сайта чтоб бот не засыпал 
def home():
    return {"status": "bot is alive 🚀"}

def run_web():
    uvicorn.run(app, host="0.0.0.0", port=8080)

threading.Thread(target=run_web).start()





async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()      #регулировщик намбер 1 крутой первый
    
    init_db()    #типо база данных что ли 
    dp.include_router(router)    #диспетчер значет регулировщика втор 
 
    await bot.delete_webhook(drop_pending_updates=True)

    load_photos()       #загружает фото в память бота 
    print("Бот запущен🚀")
    asyncio.create_task(phrase_sender(bot))  #отправляет фразочки пользователям
    asyncio.create_task(prediction_worker(bot))   #отправляет предсказания 
    
    asyncio.create_task(photo_sender(bot)) # отправляет фото пользователям 
    
    await dp.start_polling(bot)   #запуск
    

if __name__ == '__main__':                       #запуск
    asyncio.run(main())
    
