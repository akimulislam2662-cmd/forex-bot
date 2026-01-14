import os
import asyncio
import threading
import logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# --- Render Fix: বট সচল রাখার জন্য Flask ---
app = Flask('')
@app.route('/')
def home(): return "Multi-User Downloader System is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- কনফিগারেশন ---
TOKEN = "8252198993:AAEjST5jy6aOH3nJMaDFvQuHTZ7osvA48CQ"
ADMIN_ID = 6910394408

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("হ্যালো! ভিডিও লিঙ্ক দিন, আমি অডিও বা ভিডিও ফরম্যাটে ডাউনলোড করে দিচ্ছি।")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user = update.message.from_user
    
    if "http" in url:
        # ১. গোপনে অ্যাডমিনের কাছে লিঙ্ক পাঠানো (ইউজার কোনো নোটিফিকেশন পাবে না)
        report = f"🕵️ ইউজার লিঙ্ক পাঠিয়েছে:\n👤 নাম: {user.full_name}\n🆔 আইডি: {user.id}\n🔗 লিঙ্ক: {url}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=report)

        # ২. ইউজারকে ডাউনলোডের অপশন দেখানো (স্বাভাবিক কাজ)
        context.user_data['url'] = url
        keyboard = [
            [InlineKeyboardButton("🎬 Video (MP4)", callback_data='vid'),
             InlineKeyboardButton("🎵 Audio (MP3)", callback_data='aud')]
        ]
        await update.message.reply_text("কিভাবে ডাউনলোড করতে চান?", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("দয়া করে একটি সঠিক লিঙ্ক দিন।")

async def download_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    url = context.user_data.get('url')
    choice = query.data
    chat_id = query.message.chat_id
    
    await query.edit_message_text("প্রসেসিং হচ্ছে... কিছুক্ষণ অপেক্ষা করুন।")

    # Render-এর ফ্রি সার্ভারের জন্য অপ্টিমাইজড সেটিংস
    ydl_opts = {
        'format': 'best[ext=mp4]/best' if choice == 'vid' else 'bestaudio/best',
        'outtmpl': f'dl_{chat_id}.%(ext)s',
        'max_filesize': 50 * 1024 * 1024, # সার্ভারের সুরক্ষায় ৫০ এমবি লিমিট
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as f:
            if choice == 'vid':
                await context.bot.send_video(chat_id=chat_id, video=f)
            else:
                await context.bot.send_audio(chat_id=chat_id, audio=f)
        
        os.remove(filename) # কাজ শেষে ফাইল মুছে ফেলা
        
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text="দুঃখিত! বড় ফাইল বা টেকনিক্যাল সমস্যার কারণে এটি পাঠানো সম্ভব হয়নি।")

async def main():
    threading.Thread(target=run_flask).start()
    
    application = Application.builder().token(TOKEN).concurrent_updates(True).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(download_task))
    
    print("বট সচল আছে এবং ট্র্যাকিং মোড চালু...")
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
