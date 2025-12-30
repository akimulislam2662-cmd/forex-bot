import os
import telebot
from google import genai
from flask import Flask, request
import PIL.Image

# এটি নিরাপদ পদ্ধতি, এখানে সরাসরি কি (Key) থাকবে না
API_TOKEN = os.environ.get('API_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_KEY')

bot = telebot.TeleBot(API_TOKEN)
client = genai.Client(api_key=GEMINI_KEY)

app = Flask(__name__)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 আপনার বট নতুন কি (Key) দিয়ে সচল হয়েছে! এখন প্রশ্ন করুন বা ছবি পাঠান।")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "📸 এনালাইসিস করা হচ্ছে...")
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("image.jpg", 'wb') as new_file:
        new_file.write(downloaded_file)
    img = PIL.Image.open("image.jpg")
    response = client.models.generate_content(model="gemini-1.5-flash", contents=["Analyze this image and explain in Bengali", img])
    bot.reply_to(message, response.text)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    response = client.models.generate_content(model="gemini-1.5-flash", contents=message.text)
    bot.reply_to(message, response.text)

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

