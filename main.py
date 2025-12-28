import telebot
import google.generativeai as genai
import requests
import os
from flask import Flask
from threading import Thread
from telebot import types

# ১. আপনার দেওয়া তথ্যসমূহ
API_TOKEN = '8541033988:AAFEGdrSP8rGQEYEdz0KJWRgMBkaF0wiQtM'
GEMINI_KEY = 'AIzaSyCjUzWaiJfLxJ1OyB1aGXOpxSZubps0ziA'
ADMIN_ID = 7133748578

# ২. সেটিংস
bot = telebot.TeleBot(API_TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
app = Flask(__name__)

# অনুমোদিত ইউজারদের লিস্ট (মেমোরিতে থাকবে, সার্ভার রিস্টার্ট দিলে আবার এডমিনকে এপ্রুভ করতে হবে)
authorized_users = set([ADMIN_ID])
pending_requests = {}

@app.route('/')
def home():
    return "AI Trading Bot is Live!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ৩. এডমিন প্যানেল ও রিকোয়েস্ট সিস্টেম
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id in authorized_users:
        bot.reply_to(message, "স্বাগতম! আমি আপনার AI ট্রেডিং অ্যাসিস্ট্যান্ট। আমাকে বাইন্যান্সের স্ক্রিনশট পাঠান, আমি অ্যানালাইসিস করে দিচ্ছি।")
    else:
        bot.send_message(user_id, "আপনার অ্যাক্সেস নেই। এডমিনের কাছে অনুমোদনের অনুরোধ পাঠানো হয়েছে। অপেক্ষা করুন।")
        # এডমিনকে জানানো
        markup = types.InlineKeyboardMarkup()
        btn_approve = types.InlineKeyboardButton("Approve ✅", callback_data=f"app_{user_id}")
        btn_reject = types.InlineKeyboardButton("Reject ❌", callback_data=f"rej_{user_id}")
        markup.add(btn_approve, btn_reject)
        
        bot.send_message(ADMIN_ID, f"নতুন ইউজার রিকোয়েস্ট!\nনাম: {message.from_user.first_name}\nআইডি: {user_id}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.from_user.id != ADMIN_ID: return
    
    action, user_id = call.data.split('_')
    user_id = int(user_id)
    
    if action == "app":
        authorized_users.add(user_id)
        bot.answer_callback_query(call.id, "ইউজার অনুমোদিত!")
        bot.send_message(user_id, "অভিনন্দন! এডমিন আপনার রিকোয়েস্ট গ্রহণ করেছেন। এখন আপনি বটটি ব্যবহার করতে পারেন।")
        bot.edit_message_text(f"ইউজার {user_id} অনুমোদিত হয়েছে।", ADMIN_ID, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "রিকোয়েস্ট বাতিল!")
        bot.send_message(user_id, "দুঃখিত, আপনার অনুরোধ বাতিল করা হয়েছে।")
        bot.edit_message_text(f"ইউজার {user_id} এর রিকোয়েস্ট বাতিল করা হয়েছে।", ADMIN_ID, call.message.message_id)

# এডমিন কর্তৃক ইউজার রিমুভ কমান্ড
@bot.message_handler(commands=['remove'])
def remove_user(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        uid = int(message.text.split()[1])
        if uid in authorized_users:
            authorized_users.remove(uid)
            bot.reply_to(message, f"ইউজার {uid} কে রিমুভ করা হয়েছে।")
            bot.send_message(uid, "আপনার অ্যাক্সেস রিমুভ করা হয়েছে।")
    except:
        bot.reply_to(message, "সঠিকভাবে লিখুন: /remove [User_ID]")

# ৪. এআই ইমেজ অ্যানালাইসিস (বাইন্যান্স স্ক্রিনশট)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.from_user.id not in authorized_users:
        bot.reply_to(message, "আপনার এই বট ব্যবহারের অনুমতি নেই।")
        return

    bot.reply_to(message, "আমি আপনার চার্টটি বিশ্লেষণ করছি, একটু সময় দিন...")
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # জেমিনি এআই দিয়ে ইমেজ প্রসেসিং
        img_data = [{'mime_type': 'image/jpeg', 'data': downloaded_file}]
        prompt = "Analyze this Binance trading chart. Tell me: 1. Market Trend (Up/Down) 2. Entry Point 3. Stop Loss 4. Take Profit. Give clear advice in Bengali."
        
        response = model.generate_content([prompt] + img_data)
        bot.send_message(message.chat.id, response.text)
    except Exception as e:
        bot.reply_to(message, f"অ্যানালাইসিস করতে সমস্যা হয়েছে। আবার চেষ্টা করুন।\nError: {str(e)}")

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    print("AI Bot is starting...")
    bot.infinity_polling()

