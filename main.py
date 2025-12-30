import os
import telebot
from google import genai
from flask import Flask, request

# Render-এর Environment variables থেকে কি (Key) গুলো নেবে
API_TOKEN = os.environ.get('API_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_KEY')

bot = telebot.TeleBot(API_TOKEN)
client = genai.Client(api_key=GEMINI_KEY)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "জি, আমি সচল আছি! আমাকে যেকোনো প্রশ্ন করুন।")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=message.text
        )
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "দুঃখিত, একটু সমস্যা হয়েছে। দয়া করে আবার চেষ্টা করুন।")

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

