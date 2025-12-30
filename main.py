import os
import telebot
from flask import Flask, request

# Render-এর Environment variables থেকে টোকেন নেবে
API_TOKEN = os.environ.get('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# কেউ /start চাপলে এই উত্তর দিবে
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "বট সচল আছে! আপনি স্টার্ট বাটন চেপেছেন।")

# কেউ যেকোনো মেসেজ দিলে এই উত্তর দিবে
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "আপনার এসএমএসটি বটের কাছে পৌঁছেছে।")

@app.route('/' + (API_TOKEN if API_TOKEN else ""), methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://' + os.environ.get('RENDER_EXTERNAL_HOSTNAME', '') + '/' + (API_TOKEN if API_TOKEN else ""))
    return "Bot is Running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))

