import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# --- Flask Server for Render ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()
# -------------------------------

TOKEN = 'আপনার_বট_টোকেন_এখানে_দিন'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('হ্যালো! আমি আপনার ভিডিও ডাউনলোডার বট। আমাকে যেকোনো ভিডিও লিঙ্ক পাঠান।')

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text('ডাউনলোড শুরু হচ্ছে, দয়া করে অপেক্ষা করুন...')
    
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'video.mp4',
            'max_filesize': 50 * 1024 * 1024, # ৫০ এমবি লিমিট
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        await update.message.reply_video(video=open('video.mp4', 'rb'))
        os.remove('video.mp4')
    except Exception as e:
        await update.message.reply_text(f'দুঃখিত, কোনো সমস্যা হয়েছে। ভিডিওটি সম্ভবত ৫০ এমবির বেশি বড়।')

if __name__ == '__main__':
    keep_alive() # এটি Render-কে অনলাইন রাখবে
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    application.run_polling()
