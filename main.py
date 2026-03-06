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
CHAT_ID = "আপনার_টেলিগ্রাম_আইডি_দিন" # অবশ্যই আপনার আইডি দিন

def fetch_and_send_news():
    url = "https://www.forexfactory.com/calendar"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        rows = soup.find_all('tr', class_='calendar__row')
        
        for row in rows:
            impact = row.find('td', class_='calendar__impact')
            if impact and (impact.find('span', class_='high') or impact.find('span', class_='medium')):
                # নিউজ টাইম ও ডিটেইলস
                news_time = row.find('td', class_='calendar__time').text.strip()
                currency = row.find('td', class_='calendar__currency').text.strip()
                event = row.find('td', class_='calendar__event').text.strip()
                
                # ১০-৩০ মিনিট আগে অ্যালার্ট
                msg = (f"🔔 **আগামী ৩০ মিনিটের মধ্যে নিউজ!**\n\n"
                       f"💰 **Currency:** {currency}\n"
                       f"📢 **Event:** {event}\n"
                       f"⏰ **Time:** {news_time}")
                bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
    except Exception as e:
        print(f"Error: {e}")

# সিডিউলার সেটআপ
schedule.every().day.at("07:00").do(fetch_and_send_news)

def run_continuously():
    while True:
        schedule.run_pending()
        time.sleep(60)

# থ্রেড চালু
threading.Thread(target=run_continuously, daemon=True).start()
bot.infinity_polling(timeout=60, long_polling_timeout=60)
