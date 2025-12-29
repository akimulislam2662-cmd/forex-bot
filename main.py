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
# ইমেজ এবং টেক্সট উভয়ের জন্য প্রো মডেল ব্যবহার করা হয়েছে
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = telebot.types.KeyboardButton("📈 প্রজেক্ট/টোকেন এনালাইসিস")
    item2 = telebot.types.KeyboardButton("🚓 জরুরি সেবা ও রক্তদান")
    markup.add(item1, item2)
    
    bot.reply_to(message, "👋 স্বাগতম! আপনি এখন যেকোনো ট্রেডিং প্রজেক্ট বা কয়েনের নাম/স্ক্রিনশট দিলে আমি সেটির *Entry, Take Profit* এবং *Stop Loss* বের করে দেব।", reply_markup=markup, parse_mode='Markdown')

# ফটো হ্যান্ডেলার (স্ক্রিনশট এনালাইসিস এর জন্য)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "📸 স্ক্রিনশটটি প্রসেসিং হচ্ছে... এআই এনালাইসিস করে সিগন্যাল তৈরি করছে।")
    
    # ছবি ডাউনলোড করা
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("image.jpg", 'wb') as new_file:
        new_file.write(downloaded_file)
    
    # ইমেজ এনালাইসিস প্রম্পট
    img = PIL.Image.open("image.jpg")
    prompt = "Analyze this crypto chart/project. Give a realistic Entry Point, 3 Take Profit targets, and 1 Stop Loss. Answer in Bengali clearly."
    
    response = model.generate_content([prompt, img])
    bot.reply_to(message, response.text)
    
    # অ্যাডমিনকে জানানো
    bot.send_message(ADMIN_ID, f"📩 নতুন স্ক্রিনশট এনালাইসিস অনুরোধ করেছেন: {message.from_user.first_name}")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text == "📈 প্রজেক্ট/টোকেন এনালাইসিস":
        bot.reply_to(message, "আপনার টোকেন বা প্রজেক্টের নাম লিখুন অথবা চার্টের স্ক্রিনশট দিন।")
    elif message.text == "🚓 জরুরি সেবা ও রক্তদান":
        bot.reply_to(message, "🚓 জরুরি: ৯৯৯\n🩸 রক্তদান: আপনার এলাকা ও গ্রুপ লিখুন।")
    else:
        bot.send_chat_action(message.chat.id, 'typing')
        prompt = f"As an expert trader, analyze this coin name or query: {message.text}. Provide Entry, Take Profit, and Stop Loss in Bengali."
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

