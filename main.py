from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import sqlite3
import aiosqlite
import os
import asyncio

# Ініціалізація FastAPI
app = FastAPI()

# Вкажи свій OpenAI API ключ тут
OPENAI_API_KEY = "your-api-key-here"

# Ініціалізація бази даних
DB_FILE = "chat_history.db"

async def init_db():
    """Створення таблиці для збереження чату"""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS chat_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT,
            bot_response TEXT
        )
        """)
        await db.commit()

# Опис структури запиту
class ChatRequest(BaseModel):
    message: str

# GPT-4 обробник
async def get_gpt_response(user_input: str):
    """Запит до OpenAI GPT-4"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_input}],
            api_key=OPENAI_API_KEY
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")

# Ендпоінт для чату
@app.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """Обробка запиту користувача і відповідь GPT-4"""
    user_message = request.message
    bot_response = await get_gpt_response(user_message)

    # Логування в базу даних
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("INSERT INTO chat_log (user_message, bot_response) VALUES (?, ?)",
                         (user_message, bot_response))
        await db.commit()

    return {"user": user_message, "bot": bot_response}

# Ендпоінт для отримання історії чату
@app.get("/history")
async def get_chat_history():
    """Отримати всі збережені повідомлення"""
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT user_message, bot_response FROM chat_log")
        history = await cursor.fetchall()
    return [{"user": row[0], "bot": row[1]} for row in history]

# Головна сторінка API
@app.get("/")
async def root():
    return {"message": "Welcome to AI Chatbot API!"}

# Запуск FastAPI сервера
if __name__ == "__main__":
    asyncio.run(init_db())  # Ініціалізуємо базу даних
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
