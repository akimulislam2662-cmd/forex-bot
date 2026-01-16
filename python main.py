import os
import threading
import google.generativeai as genai
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# আপনার তথ্যসমূহ
BOT_TOKEN = "8293431770:AAFd8t2vTQkxkKmLCK1_LIB-uaNDrC9Zpeo" 
GEMINI_KEY = "AIzaSyDp95ZgLljgYL8OIXyOc6lquEBI1KJA1-c"

# AI কনফিগারেশন
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask('')

@app.route('/')
def home():
    return "All-in-One AI Bot is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # টেক্সট মেসেজ (ট্রেডিং প্রশ্ন বা অন্য কিছু)
    if update.message.text:
        try:
            response = model.generate_content(update.message.text)
            await update.message.reply_text(response.text)
        except Exception as e:
            print(f"Error: {e}")

    # ছবি (ট্রেডিং চার্ট অ্যানালাইসিস বা এডিট ইন্সট্রাকশন)
    elif update.message.photo:
        try:
            photo_file = await update.message.photo[-1].get_file()
            photo_path = "user_input.jpg"
            await photo_file.download_to_drive(photo_path)
            
            with open(photo_path, "rb") as f:
                img_data = f.read()
                
            contents = [
                "এই ছবিটি বিশ্লেষণ করো। ট্রেডিং চার্ট হলে প্রপার সিগন্যাল দাও, আর এডিট করতে বললে নিয়ম বলে দাও।",
                {"mime_type": "image/jpeg", "data": img_data}
            ]
            response = model.generate_content(contents)
            await update.message.reply_text(response.text)
            os.remove(photo_path)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    
    # পোলিং শুরু (Conflict এড়াতে drop_updates ব্যবহার করা হয়েছে)
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    
    print("Bot is starting freshly...")
    app_bot.run_polling(drop_pending_updates=True)
