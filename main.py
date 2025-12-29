import os
import telebot
import google.generativeai as genai
from flask import Flask, request
import PIL.Image

# কনফিগারেশন
API_TOKEN = "8017560245:AAFpNqvbbNjbf9ZqPLQG6YvbQUkTQVh-Cfo"
GEMINI_KEY = "AIzaSyB3uNOhejoG97t7zV7SQ8uSfIxtoyR3jWQ"
ADMIN_ID = 6910394408

bot = telebot.TeleBot(API_TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = telebot.types.KeyboardButton("📈 প্রজেক্ট/টোকেন এনালাইসিস")
    item2 = telebot.types.KeyboardButton("🚓 জরুরি সেবা ও রক্তদান")
    item3 = telebot.types.KeyboardButton("🚀 ক্যারিয়ার ও ইনকাম গাইড")
    markup.add(item1, item2, item3)
    
    welcome_text = (
        "👋 *আসসালামু আলাইকুম!*\n\n"
        "এটি আপনার অল-ইন-ওয়ান এআই অ্যাসিস্ট্যান্ট। এখানে আপনি পাবেন:\n"
        "✅ বাইনান্স ফিউচার সিগন্যাল (ছবি বা নাম দিলে)\n"
        "✅ জরুরি পুলিশ ও রক্তদান সেবা\n"
        "✅ ক্যারিয়ার ও অনলাইন ইনকাম গাইড"
    )
    bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "📸 আপনার স্ক্রিনশটটি এনালাইসিস করা হচ্ছে... একটু অপেক্ষা করুন।")
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("image.jpg", 'wb') as new_file:
        new_file.write(downloaded_file)
    
    img = PIL.Image.open("image.jpg")
    prompt = "Analyze this crypto chart or project. Give Entry Point, 3 Take Profits, and 1 Stop Loss clearly in Bengali."
    response = model.generate_content([prompt, img])
    bot.reply_to(message, response.text)

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    if message.text == "📈 প্রজেক্ট/টোকেন এনালাইসিস":
        bot.reply_to(message, "কয়েনের নাম লিখুন অথবা চার্টের স্ক্রিনশট দিন।")
    elif message.text == "🚓 জরুরি সেবা ও রক্তদান":
        bot.reply_to(message, "🚨 জরুরি: ৯৯৯ | 🩸 রক্তদান: আপনার গ্রুপ ও এলাকা লিখুন।")
    else:
        bot.send_chat_action(message.chat.id, 'typing')
        prompt = f"User says: {message.text}. As a professional guide and trader, answer in Bengali."
        response = model.generate_content(prompt)
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
