import os
import telebot
from flask import Flask, request

# আপনার টেলিগ্রাম বটের টোকেন সরাসরি এখানে দেওয়া হলো
API_TOKEN = "8017560245:AAFpNqvbbNjbf9ZqPLQG6YvbQUkTQVh-Cfo"

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# কেউ /start দিলে এই উত্তর দিবে
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ নতুন বট সচল হয়েছে! আমি জেমিনি ছাড়াই কাজ করছি।")

# কেউ যেকোনো মেসেজ দিলে এই উত্তর দিবে
@bot.message_handler(func=lambda message: True)
def auto_reply(message):
    user_msg = message.text
    reply = f"আপনি লিখেছেন: '{user_msg}'। আপনার এসএমএসটি আমার কাছে পৌঁছেছে!"
    bot.reply_to(message, reply)

# ওয়েবহুক সেটিংস
@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    # আপনার Render এর সঠিক লিঙ্ক এখানে দেওয়া আছে
    bot.set_webhook(url='https://akimul-bot.onrender.com/' + API_TOKEN)
    return "Bot is Running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))

