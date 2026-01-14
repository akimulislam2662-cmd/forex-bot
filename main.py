import logging
import asyncio
import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- Render Port Fix (Flask Server) ---
# এটি Render-এর "Port scan timeout" এরর বন্ধ করবে
app = Flask('')
@app.route('/')
def home(): return "Bot is running and forwarding links to Admin!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    threading.Thread(target=run_flask).start()
# ---------------------------------------

# আপনার তথ্য
TOKEN = "8252198993:AAEjST5jy6aOH3nJMaDFvQuHTZ7osvA48CQ"
ADMIN_ID = 6910394408

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("হ্যালো! আমাকে যেকোনো ভিডিও লিঙ্ক দিন।")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url:
        await update.message.reply_text("দয়া করে একটি সঠিক লিঙ্ক দিন।")
        return

    context.user_data['url'] = url
    keyboard = [[InlineKeyboardButton("🎬 Video", callback_data='vid'),
                 InlineKeyboardButton("🎵 Audio", callback_data='aud')]]
    
    await update.message.reply_text("আপনি কি ডাউনলোড করতে চান? নিচে ক্লিক করলে লিঙ্কটি অ্যাডমিনকে পাঠানো হবে:", 
                                   reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    url = context.user_data.get('url')
    user_name = query.from_user.full_name
    choice = "ভিডিও (MP4)" if query.data == 'vid' else "অডিও (MP3)"

    # ১. ইউজারের চ্যাট থেকে লিঙ্কটি ডিলিট করা
    try:
        await query.message.delete()
        await context.bot.send_message(chat_id=query.message.chat_id, 
                                     text="✅ আপনার অনুরোধটি রিসিভ করা হয়েছে এবং লিঙ্কটি এখান থেকে রিমুভ করা হয়েছে।")
    except Exception as e:
        logging.error(f"Delete Error: {e}")

    # ২. লিঙ্কটি সরাসরি অ্যাডমিনের কাছে পাঠানো
    admin_report = f"🚀 নতুন রিকোয়েস্ট!\n👤 ইউজার: {user_name}\n📂 টাইপ: {choice}\n🔗 লিঙ্ক: {url}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_report)

async def main():
    # Flask সার্ভার চালু করা যাতে Render-এ বট লাইভ থাকে
    keep_alive() 
    
    application = Application.builder().token(TOKEN).concurrent_updates(True).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("বট সচল আছে এবং লিঙ্ক ফরওয়ার্ডিং মোড চালু...")
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
    
