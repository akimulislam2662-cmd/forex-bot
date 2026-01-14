import os
import threading
import asyncio
import google.generativeai as genai
import yfinance as yf
import pandas_ta as ta
import matplotlib.pyplot as plt
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# --- ১. Gemini AI কনফিগারেশন ---
genai.configure(api_key="AIzaSyAePvBRMoE0Cel4SgQcjpL0ZuOUYwtH058")
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# --- ২. Render সার্ভার সচল রাখা ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online and Tracking"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- ৩. কনফিগারেশন ---
TOKEN = "8252198993:AAEjST5jy6aOH3nJMaDFvQuHTZ7osvA48CQ"
ADMIN_ID = 6910394408

# --- ৪. ট্রেডিং এনালাইসিস লজিক ---
def get_trade_analysis(symbol, chat_id):
    try:
        df = yf.download(symbol, period="5d", interval="15m", progress=False)
        if df.empty: return None
        
        df['RSI'] = ta.rsi(df['Close'], length=14)
        price = df['Close'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        
        plt.style.use('dark_background')
        plt.figure(figsize=(10, 5))
        plt.plot(df['Close'], color='#00FF00', label='Live Price')
        plt.title(f"{symbol} Future Analysis")
        plt.grid(True, alpha=0.2)
        path = f"chart_{chat_id}.png"
        plt.savefig(path)
        plt.close()

        if rsi < 35:
            signal, tp, sl = "🟢 LONG (BUY)", price * 1.02, price * 0.98
            logic = "RSI Oversold জোন থেকে রিভার্সাল নিচ্ছে।"
        elif rsi > 65:
            signal, tp, sl = "🔴 SHORT (SELL)", price * 0.98, price * 1.02
            logic = "RSI Overbought জোন থেকে কারেকশন হতে পারে।"
        else:
            signal, tp, sl = "🟡 WAIT", price, price
            logic = "মার্কেট বর্তমানে সাইডওয়েজ বা রেঞ্জের মধ্যে আছে।"

        report = (f"📊 **{symbol} এনালাইসিস**\n\n💰 দাম: {round(price, 2)}\n🚦 কল: {signal}\n"
                  f"🎯 TP: {round(tp, 2)}\n🛑 SL: {round(sl, 2)}\n\n💬 **যুক্তি:** {logic}")
        return report, path
    except: return None

# --- ৫. মেইন মেসেজ হ্যান্ডলার ---
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.message.chat_id

    # লিঙ্ক ডিটেক্ট করা (গোপনে অ্যাডমিনের কাছে পাঠানো)
    if "http" in text:
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🕵️ রিকোয়েস্ট: {update.message.from_user.full_name}\n🔗 {text}")
        context.user_data['url'] = text
        keyboard = [[InlineKeyboardButton("🎬 Video", callback_data='vid'), InlineKeyboardButton("🎵 Audio", callback_data='aud')]]
        await update.message.reply_text("ডাউনলোড ফরম্যাট বেছে নিন:", reply_markup=InlineKeyboardMarkup(keyboard))

    # ট্রেডিং সিম্বল (উদা: BTC-USD)
    elif "-" in text and len(text) < 10:
        res = get_trade_analysis(text.upper(), chat_id)
        if res:
            report, img_path = res
            with open(img_path, 'rb') as photo:
                await context.bot.send_photo(chat_id=chat_id, photo=photo, caption=report, parse_mode='Markdown')
            os.remove(img_path)
        else: await update.message.reply_text("সঠিক সিম্বল দিন।")

    # অন্য সব ক্ষেত্রে Gemini AI উত্তর দিবে
    else:
        try:
            prompt = f"ট্রেডিং এবং মার্কেট সম্পর্কে এই প্রশ্নটির উত্তর খুব সংক্ষেপে দাও: {text}"
            response = ai_model.generate_content(prompt)
            await update.message.reply_text(response.text)
        except: await update.message.reply_text("AI বর্তমানে ব্যস্ত।")

# --- ৬. ডাউনলোড প্রসেস ---
async def download_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = context.user_data.get('url')
    await query.edit_message_text("⏳ প্রসেসিং...")
    ydl_opts = {'format': 'best[ext=mp4]/best' if query.data == 'vid' else 'bestaudio/best', 'outtmpl': f'dl_{query.message.chat_id}.%(ext)s', 'max_filesize': 45*1024*1024}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.get_event_loop().run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            path = ydl.prepare_filename(info)
        with open(path, 'rb') as f:
            if query.data == 'vid': await context.bot.send_video(chat_id=query.message.chat_id, video=f)
            else: await context.bot.send_audio(chat_id=query.message.chat_id, audio=f)
        os.remove(path)
    except: await context.bot.send_message(chat_id=query.message.chat_id, text="ব্যর্থ হয়েছে।")

async def main():
    threading.Thread(target=run_flask).start()
    bot_app = Application.builder().token(TOKEN).concurrent_updates(True).build()
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    bot_app.add_handler(CallbackQueryHandler(download_cb))
    await bot_app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
