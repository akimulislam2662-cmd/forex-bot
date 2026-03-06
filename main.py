import telebot
import requests
from bs4 import BeautifulSoup
import datetime
import pytz
import time
import threading

# আপনার টেলিগ্রাম বট টোকেন
TOKEN = '8473264942:AAH1UXgN3ql0Jx2CnyYybfUu6X7eAF4Xsco'
bot = telebot.TeleBot(TOKEN)

# কারেন্সি ও ইমোজি ডাটা
MARKET_INFO = {
    'USD': '🇺🇸', 'EUR': '🇪🇺', 'GBP': '🇬🇧', 'JPY': '🇯🇵', 
    'AUD': '🇦🇺', 'CAD': '🇨🇦', 'CHF': '🇨🇭', 'NZD': '🇳🇿'
}

def get_forex_news():
    url = "https://www.forexfactory.com/calendar"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        rows = soup.find_all('tr', class_='calendar__row')
        
        extracted_news = []
        for row in rows:
            impact_tag = row.find('td', class_='calendar__impact')
            is_high = impact_tag and impact_tag.find('span', class_='high')
            is_medium = impact_tag and impact_tag.find('span', class_='medium')
            
            if is_high or is_medium:
                currency = row.find('td', class_='calendar__currency').text.strip()
                event = row.find('td', class_='calendar__event').text.strip()
                actual = row.find('td', class_='calendar__actual').text.strip()
                forecast = row.find('td', class_='calendar__forecast').text.strip()
                impact_type = "🔴 HIGH" if is_high else "🟠 MEDIUM"
                
                extracted_news.append({
                    'currency': currency, 'event': event, 'actual': actual, 
                    'forecast': forecast, 'impact': impact_type
                })
        return extracted_news
    except:
        return []

def result_checker(chat_id, currency, actual, forecast):
    """নিউজ টাইম শেষ হওয়ার পর প্রফিট/লস চেক করার ফাংশন"""
    time.sleep(10) # নিউজের ৫-১০ সেকেন্ড পর রেজাল্ট চেক করবে
    
    try:
        act_val = float(actual.replace('%', '').replace('k', '').replace('M', ''))
        for_val = float(forecast.replace('%', '').replace('k', '').replace('M', ''))
        
        emoji = MARKET_INFO.get(currency, '📊')
        
        if act_val > for_val:
            res_msg = f"✅ **PROFIT CONFIRMED!**\n{emoji} {currency} নিউজটি প্রফিট হয়েছে। মার্কেট শক্তিশালীভাবে উপরে গেছে! 🚀"
        elif act_val < for_val:
            res_msg = f"❌ **MARKET REVERSED!**\n{emoji} {currency} নিউজটি প্রফিট দিয়েছে। মার্কেট নিচে নেমে গেছে! 📉"
        else:
            res_msg = f"🟡 **STABLE!**\nনিউজ রেজাল্ট নিউট্রাল ছিল।"
            
        bot.send_message(chat_id, res_msg, parse_mode='Markdown')
    except:
        bot.send_message(chat_id, "⚠️ রেজাল্ট ক্যালকুলেট করা সম্ভব হয়নি।")

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "🔥 **Quotex Unique News Bot** 🔥\n\n"
                          "আমি Forex Factory থেকে হাই ও মিডিয়াম নিউজ এনালাইসিস করি এবং রেজাল্ট শেষে প্রফিট আপডেট দেই।\n"
                          "চেক করতে টাইপ করুন: `/check`", parse_mode='Markdown')

@bot.message_handler(commands=['check'])
def check(message):
    bot.send_message(message.chat.id, "🔍 নিউজ ডাটা স্ক্যান করছি...")
    news_list = get_forex_news()
    
    if not news_list:
        bot.send_message(message.chat.id, "✅ এখন কোনো বড় নিউজ নেই।")
        return

    for item in news_list:
        if item['actual']: # যদি নিউজ পাবলিশ হয়ে থাকে
            emoji = MARKET_INFO.get(item['currency'], '📊')
            bd_time = datetime.datetime.now(pytz.timezone('Asia/Dhaka')).strftime('%I:%M %p')
            
            direction = "UP ⬆️" if item['actual'] > item['forecast'] else "DOWN ⬇️"
            
            msg = (
                f"{item['impact']} **ANALYSIS**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"{emoji} **Market:** {item['currency']}\n"
                f"📊 **Actual:** {item['actual']}\n"
                f"📉 **Forecast:** {item['forecast']}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 **Prediction:** {direction}\n"
                f"⏰ **Time:** {bd_time}\n"
            )
            bot.send_message(message.chat.id, msg, parse_mode='Markdown')
            
            # রেজাল্ট চেকার রান করা (Threading ব্যবহার করে যাতে বট আটকে না যায়)
            threading.Thread(target=result_checker, args=(message.chat.id, item['currency'], item['actual'], item['forecast'])).start()

bot.polling()
