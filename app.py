import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from video_utils import get_video_info, download_video

# Переменные окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("TELEGRAM_API_ID", "0"))
API_HASH = os.environ.get("TELEGRAM_API_HASH")

app = Client(
    "supasaver_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

url_storage = {}

@app.on_message(filters.command("start"))
async def cmd_start(client, message):
    await message.reply_text("👋 Привет! Отправь мне ссылку на видео (YouTube, Instagram, TikTok, Pinterest), и я помогу его скачать.")

@app.on_message(filters.regex(r'http[s]?://'))
async def handle_link(client, message):
    url = message.text
    msg = await message.reply_text("🔍 Ищу информацию о видео...")
    
    info = await asyncio.to_thread(get_video_info, url)
    
    if not info:
        return await msg.edit_text("❌ Не удалось получить информацию. Возможно, профиль закрыт приватностью или ссылка неверна.")
    
    if "error" in info:
        return await msg.edit_text(f"❌ Ошибка получения видео:\n`{info['error']}`")
        
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 360p", callback_data="dl|360"),
            InlineKeyboardButton("🎬 480p", callback_data="dl|480")
        ],
        [
            InlineKeyboardButton("🎬 720p", callback_data="dl|720"),
            InlineKeyboardButton("🎬 1080p", callback_data="dl|1080")
        ],
        [InlineKeyboardButton("🎵 Audio", callback_data="dl|audio")]
    ])
    
    await msg.delete()
    if info.get('thumbnail'):
        sent_msg = await message.reply_photo(
            photo=info['thumbnail'],
            caption=f"🎥 **{info['title']}**\n\nВыберите качество:",
            reply_markup=keyboard
        )
    else:
        sent_msg = await message.reply_text(
            text=f"🎥 **{info['title']}**\n\nВыберите качество:",
            reply_markup=keyboard
        )
        
    url_storage[sent_msg.id] = url

@app.on_callback_query(filters.regex(r"^dl\|"))
async def handle_download(client, callback):
    quality = callback.data.split("|")[1]
    url = url_storage.get(callback.message.id)
    
    if not url:
        return await callback.answer("⏳ Ссылка устарела. Отправьте её заново.", show_alert=True)
    
    await callback.message.edit_caption("⏳ Скачиваю видео... Это может занять некоторое время.")
    
    if quality == "audio":
        format_code = 'bestaudio/best'
    else:
        format_code = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]'
    
    filename = f"temp_{callback.from_user.id}_{callback.message.id}.mp4"
    
    try:
        await asyncio.to_thread(download_video, url, format_code, filename)
        
        await callback.message.edit_caption("📤 Загружаю файл в Telegram...")
        
        if quality == "audio":
            await callback.message.reply_audio(audio=filename)
        else:
            await callback.message.reply_video(video=filename)
            
        await callback.message.delete()
        
    except Exception as e:
        await callback.message.edit_caption(f"❌ Ошибка скачивания:\n`{str(e)}`")
        print(f"Ошибка: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)
        url_storage.pop(callback.message.id, None)

# --- Блок для Render (Микро веб-сервер против отключений и API для куки) ---
from aiohttp import web

COOKIE_SECRET = os.environ.get("COOKIE_SECRET", "supasaver_super_secret_123")

async def health_check(request):
    return web.Response(text="Bot is running!")

async def update_cookies(request):
    secret = request.headers.get("X-Secret-Token")
    if secret != COOKIE_SECRET:
        return web.Response(status=403, text="Forbidden: Неверный токен")
    
    data = await request.text()
    if not data:
        return web.Response(status=400, text="No cookie data provided")
        
    # Записываем свежие куки
    with open("cookies.txt", "w", encoding="utf-8") as f:
        f.write(data)
        
    print("✅ Свежие куки успешно загружены на сервер через API!")
    return web.Response(text="Cookies updated successfully!")

async def run_dummy_server():
    app_web = web.Application()
    app_web.router.add_get('/', health_check)
    app_web.router.add_post('/update_cookies', update_cookies)
    runner = web.AppRunner(app_web)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Веб-сервер запущен на порту {port}")

if __name__ == "__main__":
    # Запускаем веб-сервер в фоне для прохождения проверок Hugging Face
    loop = asyncio.get_event_loop()
    loop.create_task(run_dummy_server())
    
    # Запускаем Telegram-бота через Pyrogram
    print("Бот запускается...")
    app.run()
