import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiohttp import web

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from video_utils import get_video_info, download_video

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")
PORT = int(os.getenv("PORT", 7860)) # Порт 7860 стандарт для Hugging Face

# Подключаем бота к ЛОКАЛЬНОМУ серверу Telegram API (порт 8081)
session = AiohttpSession(
    api=TelegramAPIServer.from_base("http://localhost:8081")
)
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

# Хранилище ссылок (Telegram ограничивает callback_data 64 байтами, 
# поэтому длинные ссылки мы храним в оперативной памяти)
url_storage = {}

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Отправь мне ссылку на видео (YouTube, Instagram, TikTok, Pinterest), "
        "и я помогу его скачать."
    )

@dp.message(F.text.regexp(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'))
async def handle_link(message: Message):
    url = message.text
    msg = await message.answer("🔍 Ищу информацию о видео...")
    
    # yt-dlp может блокировать поток, поэтому запускаем его асинхронно
    info = await asyncio.to_thread(get_video_info, url)
    
    if not info:
        return await msg.edit_text("❌ Не удалось получить информацию. Возможно, профиль закрыт приватностью или ссылка неверна.")
    
    if "error" in info:
        return await msg.edit_text(f"❌ Ошибка получения видео:\n<code>{info['error']}</code>", parse_mode="HTML")
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 360p", callback_data="dl|360"),
            InlineKeyboardButton(text="🎬 480p", callback_data="dl|480")
        ],
        [
            InlineKeyboardButton(text="🎬 720p", callback_data="dl|720"),
            InlineKeyboardButton(text="🎬 1080p", callback_data="dl|1080")
        ],
        [InlineKeyboardButton(text="🎵 Audio", callback_data="dl|audio")]
    ])
    
    await msg.delete()
    
    # Отправляем фото и кнопки
    if info.get('thumbnail'):
        sent_msg = await message.answer_photo(
            photo=info['thumbnail'],
            caption=f"🎥 <b>{info['title']}</b>\n\nВыберите качество:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        sent_msg = await message.answer(
            text=f"🎥 <b>{info['title']}</b>\n\nВыберите качество:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    # Сохраняем ссылку, привязав её к ID отправленного сообщения с кнопками
    url_storage[sent_msg.message_id] = url

@dp.callback_query(F.data.startswith("dl|"))
async def handle_download(callback: CallbackQuery):
    quality = callback.data.split("|")[1]
    
    # Достаем ссылку из хранилища
    url = url_storage.get(callback.message.message_id)
    
    if not url:
        return await callback.answer("⏳ Ссылка устарела. Отправьте её заново.", show_alert=True)
    
    await callback.message.edit_caption(caption="⏳ Скачиваю видео... Это может занять некоторое время.")
    
    # Настройки формата загрузки
    if quality == "audio":
        format_code = 'bestaudio/best'
    else:
        format_code = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]'
    
    filename = f"temp_{callback.from_user.id}_{callback.message.message_id}.mp4"
    
    try:
        # Скачиваем файл в фоне
        await asyncio.to_thread(download_video, url, format_code, filename)
        
        await callback.message.edit_caption(caption="📤 Загружаю файл в Telegram...")
        file_to_send = FSInputFile(filename)
        
        if quality == "audio":
            await callback.message.answer_audio(file_to_send)
        else:
            await callback.message.answer_video(file_to_send)
            
        await callback.message.delete()
        
    except Exception as e:
        await callback.message.edit_caption(caption="❌ Ошибка скачивания. Возможно, файл больше 50 МБ (лимит Telegram) или видео недоступно.")
        print(f"Ошибка: {e}")
    finally:
        # Очистка
        if os.path.exists(filename):
            os.remove(filename)
        url_storage.pop(callback.message.message_id, None)

# --- Блок для Render.com (Микро веб-сервер) ---
async def handle_health_check(request):
    return web.Response(text="Бот работает!")

async def main():
    # Запускаем фоновый веб-сервер, чтобы Render не выключал приложение
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"Веб-сервер запущен на порту {PORT} (Для Render)")
    
    # Запускаем самого бота
    print("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
