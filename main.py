import telebot
import requests
from bs4 import BeautifulSoup
import os
from flask import Flask
from threading import Thread

# ১. আপনার তথ্য (বট টোকেন এবং আপনার আইডি)
API_TOKEN = '8473264942:AAGCVVYzBWfH775LZ7gekhXsf5vMNdFrvZw'
ADMIN_ID = 6910394408

bot = telebot.TeleBot(API_TOKEN)
app = Flask('')

# ২. Render-এর পোর্টের সমস্যা সমাধান (যাতে অফলাইন না হয়)
@app.route('/')
def home():
    return "Bot is Live!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ৩. ফরেক্স নিউজ ডাটা সংগ্রহের ফাংশন
def get_forex_news():
    url = "https://www.forexfactory.com/calendar"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        news_list = []
        rows = soup.select(".calendar__row")
        
        for row in rows:
            impact_cell = row.select_one(".calendar__impact span")
            if impact_cell:
                impact = impact_cell.get('class', [""])[1]
                # হাই এবং মিডিয়াম ইমপ্যাক্ট নিউজ ফিল্টার
                if 'high' in impact or 'medium' in impact:
                    curr = row.select_one(".calendar__currency").text.strip()
                    event = row.select_one(".calendar__event").text.strip()
                    time_val = row.select_one(".calendar__time").text.strip()
                    actual = row.select_one(".calendar__actual").text.strip()
                    forecast = row.select_one(".calendar__forecast").text.strip()
                    
                    signal, advice = "⏳ WAITING", "ডাটা আসার অপেক্ষায়..."
                    if actual and forecast:
                        try:
                            act_num = float(actual.replace('%', '').replace('k', '').replace('M', '').replace(',', ''))
                            for_num = float(forecast.replace('%', '').replace('k', '').replace('M', '').replace(',', ''))
                            pairs = "EURUSD, GBPUSD" if curr == "USD" else f"{curr}USD"
                            
                            if act_num > for_num:
                                signal, advice = "🚀 UP (BUY)", f"✅ {curr} শক্তিশালী। {pairs} এ বাই সুযোগ।"
                            elif act_num < for_num:
                                signal, advice = "🔻 DOWN (SELL)", f"❌ {curr} দুর্বল। {pairs} এ সেল সুযোগ।"
                        except: pass
                    
                    news_list.append(f"⏰ {time_val} | 💱 **{curr}**\n📊 {event}\n🔥 **SIGNAL: {signal}**\n📝 {advice}\n---")
        
        return "\n\n".join(news_list[:8]) if news_list else "বর্তমানে কোনো বড় নিউজ নেই।"
    except:
        return "সার্ভার থেকে ডাটা আনতে সমস্যা হয়েছে।"

# ৪. বটের কমান্ড হ্যান্ডলার
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "স্বাগতম! ফরেক্স নিউজ ও সিগন্যাল পেতে /news লিখুন।")

@bot.message_handler(commands=['news'])
def send_news(message):
    bot.send_message(message.chat.id, "অপেক্ষা করুন, লেটেস্ট মার্কেট ডাটা চেক করছি...")
    news_content = get_forex_news()
    bot.send_message(message.chat.id, news_content, parse_mode="Markdown")

# ৫. বট চালু করার মেইন ফাংশন
if __name__ == "__main__":
    # ওয়েব সার্ভার আলাদা থ্রেডে চালানো (Render-এর জন্য জরুরি)
    t = Thread(target=run_web)
    t.start()
    
    # টেলিগ্রাম বট স্টার্ট করা
    print("Bot is starting...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
