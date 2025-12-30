import os
import telebot
from google import genai
from flask import Flask, request
import PIL.Image

# আপনার এপিআই কিগুলো এখানে দেওয়া আছে
API_TOKEN = "8017560245:AAFpNqvbbNjbf9ZqPLQG6YvbQUkTQVh-Cfo"
GEMINI_KEY = "AIzaSyB3uNOhejoG97t7zV7SQ8uSfIxtoyR3jWQ"

bot = telebot.TeleBot(API_TOKEN)
client = genai.Client(api_key=GEMINI_KEY)

app = Flask(__name__)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 আসসালামু আলাইকুম! আপনার এআই বট এখন সচল। যেকোনো প্রশ্ন করুন বা চার্টের ছবি দিন।")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "📸 ছবি এনালাইসিস করা হচ্ছে...")
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("image.jpg", 'wb') as new_file:
        new_file.write(downloaded_file)
    
    img = PIL.Image.open("image.jpg")
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=["Analyze this crypto chart and give entry/exit points in Bengali", img]
    )
    bot.reply_to(message, response.text)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=message.text
    )
    bot.reply_to(message, response.text)

@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://' + os.environ.get('RENDER_EXTERNAL_HOSTNAME') + '/' + API_TOKEN)
    return "Bot is Running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))

