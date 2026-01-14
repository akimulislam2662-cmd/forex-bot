import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- ১. Render-এর জন্য Flask সার্ভার (গোপন রাখার জন্য) ---
app = Flask('')
@app.route('/')
def home(): return "System is Online"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- ২. বটের তথ্য ---
TOKEN = "8252198993:AAEjST5jy6aOH3nJMaDFvQuHTZ7osvA48CQ"
ADMIN_ID = 6910394408

async def track_and_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user = update.message.from_user
    
    # যদি মেসেজে কোনো লিঙ্ক থাকে
    if "http" in user_text:
        # অ্যাডমিনের কাছে গোপন রিপোর্ট পাঠানো
        report = (
            f"🕵️ নতুন লিঙ্ক পাওয়া গেছে!\n\n"
            f"👤 ইউজার: {user.full_name}\n"
            f"🔗 লিঙ্ক: {user_text}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=report)
        
        # ইউজার যাতে বুঝতে না পারে, তাই তার পাঠানো লিঙ্কটি গ্রুপ থেকে ডিলিট করে দেওয়া
        try:
            await update.message.delete()
        except:
            pass # বট যদি অ্যাডমিন না হয় তবে ডিলিট হবে না

async def main():
    threading.Thread(target=run_flask).start() # সার্ভার চালু
    
    application = Application.builder().token(TOKEN).build()
    
    # সব টেক্সট মেসেজ চেক করবে
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_and_delete))
    
    print("বটটি গোপনে কাজ শুরু করেছে...")
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
