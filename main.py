import telebot
import requests
from bs4 import BeautifulSoup
import datetime
import pytz
import schedule
import time
import threading

TOKEN = '8473264942:AAH1UXgN3ql0Jx2CnyYybfUu6X7eAF4Xsco'
bot = telebot.TeleBot(TOKEN)
CHAT_ID = "আপনার_টেলিগ্রাম_আইডি_বা_গ্রুপ_আইডি" # এখানে আপনার চ্যাট আইডি দিন

def get_full_day_news():
    url = "https://www.forexfactory.com/calendar"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        rows = soup.find_all('tr', class_='calendar__row')
        
        daily_list = []
        for row in rows:
            impact_tag = row.find('td', class_='calendar__impact')
            if impact_tag and (impact_tag.find('span', class_='high') or impact_tag.find('span', class_='medium')):
                time_val = row.find('td', class_='calendar__time').text.strip()
                currency = row.find('td', class_='calendar__currency').text.strip()
                event = row.find('td', class_='calendar__event').text.strip()
                
                daily_list.append(f"⏰ {time_val} | 💰 {currency} | 📢 {event}")
        return daily_list
    except:
        return []

def send_daily_summary():
    news = get_full_day_news()
    if news:
        msg = "🗓 **আজকের সকল হাই ও মিডিয়াম নিউজ সিগন্যাল:**\n\n" + "\n".join(news)
        bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
    else:
        bot.send_message(CHAT_ID, "✅ আজ কোনো বড় নিউজ নেই।")

# অটোমেশন লুপ
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

schedule.every().day.at("07:00").do(send_daily_summary)
threading.Thread(target=run_scheduler, daemon=True).start()

@bot.message_handler(commands=['start', 'check'])
def start_bot(message):
    bot.reply_to(message, "🚀 বট সক্রিয়! আমি আপনাকে প্রতিদিনের নিউজ ও মার্কেটের আপডেট দিব।")

bot.infinity_polling()
