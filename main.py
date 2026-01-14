import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- Render Port Fix (Flask Server) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive & Secure!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    threading.Thread(target=run_flask).start()
# ---------------------------------------

TOKEN = '8252198993:AAEjST5jy6aOH3nJMaDFvQuHTZ7osvA48CQ'
ADMIN_ID = 6910394408

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('হ্যালো! ভিডিও লিঙ্ক পাঠান।')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" in url:
        keyboard = [
            [InlineKeyboardButton("MP4 (Video)", callback_data=f"video|{url}")],
            [InlineKeyboardButton("MP3 (Audio)", callback_data=f"audio|{url}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("ডাউনলোড অপশন বেছে নিন:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("দয়া করে একটি সঠিক লিঙ্ক পাঠান।")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.query
    await query.answer()
    
    data = query.data.split("|")
    choice = data[0]
    link = data[1]
    user_name = query.from_user.full_name

    # ১. ইউজারের চ্যাট থেকে লিঙ্ক এবং বাটন সম্বলিত মেসেজটি মুছে ফেলা (Remote/Remove)
    try:
        await query.message.delete()
        await context.bot.send_message(chat_id=query.message.chat_id, text="✅ আপনার লিঙ্কটি প্রসেস করার জন্য অ্যাডমিনের কাছে পাঠানো হয়েছে এবং এখান থেকে রিমুভ করা হয়েছে।")
    except Exception as e:
        print(f"Delete error: {e}")

    # ২. লিঙ্কটি সরাসরি অ্যাডমিনের (আপনার) কাছে পাঠানো
    report = f"🚀 নতুন রিকোয়েস্ট!\n👤 ইউজার: {user_name}\n📂 টাইপ: {choice}\n🔗 লিঙ্ক: {link}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=report)

if __name__ == '__main__':
    keep_alive()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_click))
    application.run_polling()
    
