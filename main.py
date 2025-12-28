import telebot
import requests
from bs4 import BeautifulSoup
from telebot import types

# আপনার তথ্য
API_TOKEN = '8473264942:AAGCVVYzBWfH775LZ7gekhXsf5vMNdFrvZw'
ADMIN_ID = 6910394408

bot = telebot.TeleBot(API_TOKEN)
authorized_users = {ADMIN_ID}

def get_real_analysis():
    url = "https://www.forexfactory.com/calendar"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(response.content, 'html.parser')
        news_list = []
        rows = soup.select(".calendar__row")
        for row in rows:
            impact_cell = row.select_one(".calendar__impact span")
            if impact_cell:
                impact = impact_cell.get('class', [""])[1]
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
                            pairs = "EURUSD, GBPUSD, USDJPY" if curr == "USD" else f"{curr}USD, {curr}JPY"
                            if act_num > for_num:
                                signal, advice = "🚀 UP (BUY)", f"✅ {curr} স্ট্রং। {pairs} এ ট্রেড নিন।"
                            elif act_num < for_num:
                                signal, advice = "🔻 DOWN (SELL)", f"❌ {curr} উইক। {pairs} এ ট্রেড নিন।"
                        except: pass
                    news_list.append(f"⏰ {time_val} | 💱 **{curr}**\n📊 {event}\n🔥 **SIGNAL: {signal}**\n📝 {advice}\n---")
        return "\n\n".join(news_list[:6]) if news_list else "নিউজ নেই।"
    except: return "সার্ভার এরর।"

@bot.message_handler(commands=['start'])
def start(message):
    u_id = message.from_user.id
    if u_id == ADMIN_ID:
        bot.send_message(message.chat.id, "স্বাগতম এডমিন! নিউজ দেখতে /news লিখুন।")
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Add User", callback_data=f"add_{u_id}"))
        bot.send_message(ADMIN_ID, f"🛎 নতুন ইউজার!\n🆔 `{u_id}`", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_'))
def callback_add(call):
    new_id = int(call.data.split('_')[1])
    authorized_users.add(new_id)
    bot.send_message(new_id, "🎉 অনুমতি পেয়েছেন! এখন /news দেখতে পারেন।")

@bot.message_handler(commands=['news'])
def send_news(message):
    if message.from_user.id in authorized_users:
        bot.send_message(message.chat.id, get_real_analysis(), parse_mode="Markdown")

if __name__ == "__main__":
    bot.infinity_polling()
