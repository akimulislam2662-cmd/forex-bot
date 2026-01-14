import logging
import asyncio
import os
import yt_dlp
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# আপনার বটের টোকেন
TOKEN = "8252198993:AAEjST5jy6aOH3nJMaDFvQuHTZ7osvA48CQ"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def extract_url(text):
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, text)
    return match.group(0) if match else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("হ্যালো! আমাকে যেকোনো ভিডিও লিঙ্ক দিন।")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = extract_url(update.message.text)
    if not url:
        await update.message.reply_text("দয়া করে একটি সঠিক লিঙ্ক দিন।")
        return
    context.user_data['url'] = url
    keyboard = [[InlineKeyboardButton("🎬 Video", callback_data='vid'), InlineKeyboardButton("🎵 Audio", callback_data='aud')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("আপনি কি ডাউনলোড করতে চান?", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = context.user_data.get('url')
    if not url: return

    choice = query.data
    user_id = update.effective_user.id
    await query.edit_message_text("প্রসেসিং হচ্ছে... কিছুক্ষণ অপেক্ষা করুন।")

    ydl_opts = {
        'format': 'best',
        'outtmpl': f'dl_{user_id}.%(ext)s',
        'max_filesize': 48 * 1024 * 1024, # ৪৮ এমবি লিমিট
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            file_path = ydl.prepare_filename(info)
            
            with open(file_path, 'rb') as f:
                if choice == 'aud':
                    await context.bot.send_audio(chat_id=user_id, audio=f, caption="আপনার অডিওটি তৈরি।")
                else:
                    await context.bot.send_video(chat_id=user_id, video=f, caption="আপনার ভিডিওটি তৈরি।")
            
            if os.path.exists(file_path):
                os.remove(file_path)

    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text="দুঃখিত! ভিডিওটি ডাউনলোড করা যাচ্ছে না।")

async def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    while True: await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())
