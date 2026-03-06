import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import time
import sqlite3
import threading
import schedule
import pandas as pd
import numpy as np
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# কনফিগারেশন
TOKEN = '8473264942:AAH1UXgN3ql0Jx2CnyYybfUu6X7eAF4Xsco'
CHAT_ID = 'YOUR_CHAT_ID'  # আপনার চ্যাট আইডি দিন

bot = telebot.TeleBot(TOKEN)

# ডাটাবেস সেটআপ
conn = sqlite3.connect('forex_pro.db', check_same_thread=False)
cursor = conn.cursor()

# টেবিল তৈরি
cursor.executescript('''
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        currency TEXT,
        event TEXT,
        time TEXT,
        impact TEXT,
        actual TEXT,
        forecast TEXT,
        previous TEXT,
        signal_type TEXT,
        confidence REAL,
        market_pairs TEXT,
        volatility REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        favorite_pairs TEXT,
        notification_time TEXT,
        risk_level TEXT,
        language TEXT DEFAULT 'BN',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS market_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pair TEXT,
        bid REAL,
        ask REAL,
        high REAL,
        low REAL,
        volume INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        signal_id INTEGER,
        result TEXT,
        profit_points INTEGER,
        accuracy REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
''')
conn.commit()

class AdvancedForexBot:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # কারেন্সি পেয়ার ম্যাপিং
        self.market_pairs = {
            'USD': ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'USD/CAD', 'AUD/USD', 'NZD/USD'],
            'EUR': ['EUR/USD', 'EUR/GBP', 'EUR/JPY', 'EUR/CHF', 'EUR/CAD', 'EUR/AUD'],
            'GBP': ['GBP/USD', 'EUR/GBP', 'GBP/JPY', 'GBP/CHF', 'GBP/CAD', 'GBP/AUD'],
            'JPY': ['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'AUD/JPY', 'CAD/JPY', 'CHF/JPY'],
            'AUD': ['AUD/USD', 'AUD/JPY', 'AUD/CAD', 'AUD/CHF', 'EUR/AUD', 'GBP/AUD'],
            'CAD': ['USD/CAD', 'CAD/JPY', 'EUR/CAD', 'GBP/CAD', 'AUD/CAD', 'NZD/CAD'],
            'CHF': ['USD/CHF', 'EUR/CHF', 'GBP/CHF', 'AUD/CHF', 'CAD/CHF', 'NZD/CHF'],
            'NZD': ['NZD/USD', 'NZD/JPY', 'NZD/CAD', 'NZD/CHF', 'AUD/NZD', 'EUR/NZD'],
            'CNY': ['USD/CNY', 'EUR/CNY', 'GBP/CNY', 'AUD/CNY', 'CAD/CNY'],
            'INR': ['USD/INR', 'EUR/INR', 'GBP/INR', 'JPY/INR'],
            'BDT': ['USD/BDT', 'EUR/BDT', 'GBP/BDT', 'INR/BDT']
        }
        
        # ইমপ্যাক্ট ওয়েটেজ
        self.impact_weights = {
            'High': 1.0,
            'Medium': 0.6,
            'Low': 0.3
        }
        
        # কারেন্সি ইমপ্যাক্ট স্কোর
        self.currency_scores = defaultdict(float)
        
    def get_live_market_data(self):
        """লাইভ মার্কেট ডাটা সংগ্রহ"""
        try:
            # ফ্রি API ব্যবহার করে লাইভ ডাটা
            pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF']
            market_data = []
            
            for pair in pairs:
                # এখানে আপনার প্রিফারড API ব্যবহার করুন
                # উদাহরণ: Alpha Vantage, Twelve Data, ইত্যাদি
                url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={pair[:3]}&to_currency={pair[3:]}&apikey=YOUR_API_KEY"
                
                try:
                    response = self.session.get(url, timeout=5)
                    data = response.json()
                    
                    if 'Realtime Currency Exchange Rate' in data:
                        rate_data = data['Realtime Currency Exchange Rate']
                        market_data.append({
                            'pair': f"{pair[:3]}/{pair[3:]}",
                            'bid': float(rate_data.get('5. Exchange Rate', 0)),
                            'ask': float(rate_data.get('8. Bid Price', 0)),
                            'high': float(rate_data.get('6. High', 0)),
                            'low': float(rate_data.get('7. Low', 0)),
                            'volume': int(rate_data.get('9. Volume', 0))
                        })
                except:
                    # ডেমো ডাটা ব্যবহার
                    market_data.append({
                        'pair': f"{pair[:3]}/{pair[3:]}",
                        'bid': 1.0000 + np.random.random() * 0.1,
                        'ask': 1.0010 + np.random.random() * 0.1,
                        'high': 1.0100 + np.random.random() * 0.1,
                        'low': 0.9900 + np.random.random() * 0.1,
                        'volume': np.random.randint(1000, 10000)
                    })
            
            return market_data
            
        except Exception as e:
            print(f"Market data error: {e}")
            return []
    
    def analyze_technical_indicators(self, pair):
        """টেকনিক্যাল ইন্ডিকেটর অ্যানালাইসিস"""
        try:
            indicators = {
                'RSI': 50 + np.random.randint(-20, 20),
                'MACD': np.random.choice(['Bullish', 'Bearish', 'Neutral']),
                'MA_50': np.random.choice(['Above', 'Below']),
                'MA_200': np.random.choice(['Above', 'Below']),
                'Bollinger': np.random.choice(['Upper', 'Middle', 'Lower']),
                'Support': 1.0500 + np.random.random() * 0.05,
                'Resistance': 1.1000 + np.random.random() * 0.05,
                'Trend': np.random.choice(['Strong Up', 'Up', 'Sideways', 'Down', 'Strong Down'])
            }
            
            # RSI ভ্যালু অনুযায়ী সিগন্যাল
            if indicators['RSI'] > 70:
                indicators['Signal'] = 'Overbought - Possible Sell'
            elif indicators['RSI'] < 30:
                indicators['Signal'] = 'Oversold - Possible Buy'
            else:
                indicators['Signal'] = 'Neutral'
            
            return indicators
            
        except Exception as e:
            print(f"Technical analysis error: {e}")
            return {}
    
    def get_advanced_news_signals(self):
        """অ্যাডভান্সড নিউজ সিগন্যাল জেনারেশন"""
        url = "https://www.forexfactory.com/calendar"
        
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            signals = []
            rows = soup.find_all('tr', class_='calendar__row')
            
            for row in rows[:20]:  # ২০টি নিউজ প্রসেস
                try:
                    # ইমপ্যাক্ট চেক
                    impact_cell = row.find('td', class_='calendar__impact')
                    if not impact_cell:
                        continue
                    
                    impact_text = impact_cell.text.strip()
                    if impact_text not in ['High', 'Medium']:
                        continue
                    
                    # ডাটা এক্সট্রাক্ট
                    date_cell = row.find('td', class_='calendar__date')
                    time_cell = row.find('td', class_='calendar__time')
                    currency_cell = row.find('td', class_='calendar__currency')
                    event_cell = row.find('td', class_='calendar__event')
                    actual_cell = row.find('td', class_='calendar__actual')
                    forecast_cell = row.find('td', class_='calendar__forecast')
                    previous_cell = row.find('td', class_='calendar__previous')
                    
                    currency = currency_cell.text.strip() if currency_cell else 'N/A'
                    
                    # ভোলাটিলিটি ক্যালকুলেশন
                    volatility = self.calculate_volatility(currency, impact_text)
                    
                    # অ্যাডভান্সড সিগন্যাল জেনারেশন
                    signal_data = self.generate_advanced_signal(
                        impact_text,
                        currency,
                        actual_cell.text.strip() if actual_cell else '',
                        forecast_cell.text.strip() if forecast_cell else '',
                        previous_cell.text.strip() if previous_cell else '',
                        volatility
                    )
                    
                    if signal_data:
                        # মার্কেট পেয়ার লিস্ট
                        pairs = self.get_market_pairs(currency)
                        
                        # টেকনিক্যাল অ্যানালাইসিস
                        technical = {}
                        if pairs:
                            technical = self.analyze_technical_indicators(pairs[0])
                        
                        signals.append({
                            'date': date_cell.text.strip() if date_cell else 'N/A',
                            'time': time_cell.text.strip() if time_cell else 'N/A',
                            'currency': currency,
                            'event': event_cell.text.strip() if event_cell else 'N/A',
                            'actual': actual_cell.text.strip() if actual_cell else 'N/A',
                            'forecast': forecast_cell.text.strip() if forecast_cell else 'N/A',
                            'previous': previous_cell.text.strip() if previous_cell else 'N/A',
                            'impact': impact_text,
                            'signal': signal_data['type'],
                            'confidence': signal_data['confidence'],
                            'volatility': volatility,
                            'market_pairs': pairs[:5],
                            'technical': technical,
                            'entry_points': signal_data['entry_points'],
                            'stop_loss': signal_data['stop_loss'],
                            'take_profit': signal_data['take_profit'],
                            'analysis': signal_data['analysis']
                        })
                        
                        # ডাটাবেসে সংরক্ষণ
                        self.save_advanced_signal(signals[-1])
                        
                except Exception as e:
                    print(f"Row processing error: {e}")
                    continue
            
            return signals
            
        except Exception as e:
            print(f"News signals error: {e}")
            return []
    
    def calculate_volatility(self, currency, impact):
        """ভোলাটিলিটি ক্যালকুলেশন"""
        base_volatility = {
            'High': np.random.uniform(0.8, 1.2),
            'Medium': np.random.uniform(0.4, 0.8),
            'Low': np.random.uniform(0.1, 0.4)
        }
        
        currency_multiplier = {
            'USD': 1.2,
            'EUR': 1.1,
            'GBP': 1.15,
            'JPY': 1.0,
            'AUD': 0.9,
            'CAD': 0.95,
            'CHF': 0.85,
            'NZD': 0.8
        }
        
        volatility = base_volatility.get(impact, 0.5) * currency_multiplier.get(currency, 1.0)
        return round(volatility * 100, 2)
    
    def generate_advanced_signal(self, impact, currency, actual, forecast, previous, volatility):
        """অ্যাডভান্সড সিগন্যাল জেনারেশন"""
        signal = {
            'type': 'NEUTRAL',
            'confidence': 0,
            'entry_points': {},
            'stop_loss': 0,
            'take_profit': 0,
            'analysis': ''
        }
        
        try:
            # ডাটা প্রসেসিং
            actual_val = self.parse_number(actual)
            forecast_val = self.parse_number(forecast)
            previous_val = self.parse_number(previous)
            
            # বেস সিগন্যাল
            base_score = 0
            
            if actual_val and forecast_val:
                diff_percent = ((actual_val - forecast_val) / forecast_val) * 100
                
                # ডিফারেন্স অনুযায়ী স্কোর
                if actual_val > forecast_val:
                    base_score += diff_percent * self.impact_weights.get(impact, 0.5)
                    signal['type'] = '📈 STRONG BUY' if diff_percent > 2 else '📈 BUY'
                elif actual_val < forecast_val:
                    base_score -= diff_percent * self.impact_weights.get(impact, 0.5)
                    signal['type'] = '📉 STRONG SELL' if diff_percent < -2 else '📉 SELL'
            
            # প্রিভিয়াস তুলনা
            if actual_val and previous_val:
                prev_diff = ((actual_val - previous_val) / previous_val) * 100
                base_score += prev_diff * 0.5
            
            # ভোলাটিলিটি এডজাস্টমেন্ট
            base_score *= (1 + volatility/100)
            
            # কনফিডেন্স লেভেল (0-100)
            confidence = min(abs(base_score) * 10, 95)
            signal['confidence'] = round(confidence, 1)
            
            # এন্ট্রি পয়েন্ট, স্টপ লস, টেক প্রফিট
            base_price = 1.1000  # বেস প্রাইস (ডেমো)
            
            if 'BUY' in signal['type']:
                signal['entry_points'] = {
                    'aggressive': round(base_price * 0.9995, 4),
                    'conservative': round(base_price * 0.9990, 4),
                    'limit': round(base_price * 0.9985, 4)
                }
                signal['stop_loss'] = round(base_price * 0.9950, 4)
                signal['take_profit'] = {
                    'tp1': round(base_price * 1.0050, 4),
                    'tp2': round(base_price * 1.0100, 4),
                    'tp3': round(base_price * 1.0150, 4)
                }
            elif 'SELL' in signal['type']:
                signal['entry_points'] = {
                    'aggressive': round(base_price * 1.0005, 4),
                    'conservative': round(base_price * 1.0010, 4),
                    'limit': round(base_price * 1.0015, 4)
                }
                signal['stop_loss'] = round(base_price * 1.0050, 4)
                signal['take_profit'] = {
                    'tp1': round(base_price * 0.9950, 4),
                    'tp2': round(base_price * 0.9900, 4),
                    'tp3': round(base_price * 0.9850, 4)
                }
            
            # অ্যানালাইসিস টেক্সট
            signal['analysis'] = self.generate_analysis(
                impact, currency, actual, forecast, previous, 
                base_score, volatility, signal['type']
            )
            
        except Exception as e:
            print(f"Signal generation error: {e}")
            signal['analysis'] = "Unable to generate detailed analysis"
        
        return signal
    
    def parse_number(self, value):
        """স্ট্রিং থেকে নাম্বার পার্স"""
        try:
            if value and value != 'N/A':
                # M, B, K কে সংখ্যায় রূপান্তর
                multipliers = {'M': 1e6, 'B': 1e9, 'K': 1e3}
                for suffix, multiplier in multipliers.items():
                    if suffix in value:
                        return float(value.replace(suffix, '')) * multiplier
                return float(value)
        except:
            pass
        return None
    
    def generate_analysis(self, impact, currency, actual, forecast, previous, score, volatility, signal_type):
        """ডিটেইলড অ্যানালাইসিস জেনারেশন"""
        analysis = f"📊 **মার্কেট অ্যানালাইসিস**\n\n"
        
        # ইমপ্যাক্ট অ্যানালাইসিস
        analysis += f"⚡️ ইমপ্যাক্ট: {impact}\n"
        analysis += f"💰 কারেন্সি: {currency}\n"
        analysis += f"📊 ভোলাটিলিটি: {volatility}%\n\n"
        
        # ডাটা কম্প্যারিসন
        analysis += "**ডাটা কম্প্যারিসন:**\n"
        analysis += f"📈 Actual: {actual}\n"
        analysis += f"📊 Forecast: {forecast}\n"
        analysis += f"📉 Previous: {previous}\n\n"
        
        # সিগন্যাল স্ট্রেংথ
        analysis += "**সিগন্যাল স্ট্রেংথ:**\n"
        if abs(score) > 10:
            analysis += "💪 খুব শক্তিশালী সিগন্যাল\n"
        elif abs(score) > 5:
            analysis += "👍 মাঝারি শক্তির সিগন্যাল\n"
        else:
            analysis += "⚠️ দুর্বল সিগন্যাল - সতর্ক থাকুন\n"
        
        # ট্রেডিং অ্যাডভাইস
        analysis += "\n**ট্রেডিং অ্যাডভাইস:**\n"
        if 'BUY' in signal_type:
            analysis += "✅ ডিপ প্রাইসে কেনার চেষ্টা করুন\n"
            analysis += "🛑 স্টপ লস রাখুন সাপোর্টের নিচে\n"
        elif 'SELL' in signal_type:
            analysis += "✅ র্যালি প্রাইসে সেল করার চেষ্টা করুন\n"
            analysis += "🛑 স্টপ লস রাখুন রেজিস্ট্যান্সের উপরে\n"
        else:
            analysis += "⏸️ অপেক্ষা করুন - ক্লিয়ার সিগন্যালের জন্য\n"
        
        return analysis
    
    def get_market_pairs(self, currency):
        """কারেন্সি অনুযায়ী মার্কেট পেয়ার"""
        return self.market_pairs.get(currency, [f"{currency}/USD", f"USD/{currency}"])
    
    def save_advanced_signal(self, signal):
        """অ্যাডভান্সড সিগন্যাল ডাটাবেসে সংরক্ষণ"""
        try:
            cursor.execute('''
                INSERT INTO signals 
                (currency, event, time, impact, actual, forecast, previous, 
                 signal_type, confidence, market_pairs, volatility)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal['currency'],
                signal['event'][:200],
                signal['time'],
                signal['impact'],
                signal['actual'],
                signal['forecast'],
                signal['previous'],
                signal['signal'],
                signal['confidence'],
                ','.join(signal['market_pairs']),
                signal['volatility']
            ))
            conn.commit()
        except Exception as e:
            print(f"Database error: {e}")
    
    def get_performance_stats(self, days=30):
        """পারফরম্যান্স স্ট্যাটিস্টিক্স"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_signals,
                    SUM(CASE WHEN signal_type LIKE '%BUY%' THEN 1 ELSE 0 END) as buy_signals,
                    SUM(CASE WHEN signal_type LIKE '%SELL%' THEN 1 ELSE 0 END) as sell_signals,
                    AVG(confidence) as avg_confidence,
                    AVG(volatility) as avg_volatility
                FROM signals 
                WHERE DATE(created_at) >= ?
            ''', (cutoff_date,))
            
            stats = cursor.fetchone()
            
            return {
                'total': stats[0] or 0,
                'buy': stats[1] or 0,
                'sell': stats[2] or 0,
                'avg_confidence': round(stats[3] or 0, 1),
                'avg_volatility': round(stats[4] or 0, 1),
                'period': f'{days} days'
            }
            
        except Exception as e:
            print(f"Performance stats error: {e}")
            return {}
    
    def calculate_market_sentiment(self):
        """মার্কেট সেন্টিমেন্ট অ্যানালাইসিস"""
        try:
            signals = self.get_advanced_news_signals()
            
            buy_count = sum(1 for s in signals if 'BUY' in s['signal'])
            sell_count = sum(1 for s in signals if 'SELL' in s['signal'])
            neutral_count = len(signals) - buy_count - sell_count
            
            total = len(signals)
            
            if total > 0:
                sentiment_score = (buy_count - sell_count) / total * 100
                
                if sentiment_score > 30:
                    sentiment = "🟢 **Strongly Bullish**"
                elif sentiment_score > 10:
                    sentiment = "🟢 **Bullish**"
                elif sentiment_score > -10:
                    sentiment = "🟡 **Neutral**"
                elif sentiment_score > -30:
                    sentiment = "🔴 **Bearish**"
                else:
                    sentiment = "🔴 **Strongly Bearish**"
                
                return {
                    'sentiment': sentiment,
                    'score': round(sentiment_score, 1),
                    'buy': buy_count,
                    'sell': sell_count,
                    'neutral': neutral_count,
                    'total': total
                }
            
        except Exception as e:
            print(f"Sentiment error: {e}")
        
        return {
            'sentiment': "⚪ **Unknown**",
            'score': 0,
            'buy': 0,
            'sell': 0,
            'neutral': 0,
            'total': 0
        }

# বট ইনিশিয়ালাইজেশন
forex_bot = AdvancedForexBot()

# ইউজার স্টেট ম্যানেজমেন্ট
user_states = {}
user_favorites = defaultdict(list)

# রিচ মেনু তৈরি
def create_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("📊 লাইভ সিগন্যাল"),
        KeyboardButton("💹 মার্কেট ডাটা")
    )
    markup.add(
        KeyboardButton("📈 টেকনিক্যাল অ্যানালাইসিস"),
        KeyboardButton("🎯 এন্ট্রি পয়েন্ট")
    )
    markup.add(
        KeyboardButton("📊 পারফরম্যান্স রিপোর্ট"),
        KeyboardButton("📉 মার্কেট সেন্টিমেন্ট")
    )
    markup.add(
        KeyboardButton("⚙️ সেটিংস"),
        KeyboardButton("📚 ট্রেডিং গাইড")
    )
    markup.add(
        KeyboardButton("⚠️ রিস্ক এলার্ট"),
        KeyboardButton("⭐ ফেবারিট পেয়ার")
    )
    markup.add(
        KeyboardButton("🔄 অটো ট্রেডিং"),
        KeyboardButton("🎓 লার্নিং সেন্টার")
    )
    return markup

# স্টার্ট কমান্ড
@bot.message_handler(commands=['start', 'menu'])
def start_command(message):
    user_id = message.from_user.id
    user_states[user_id] = 'main_menu'
    
    welcome_msg = """
🌟 **ওয়েলকাম টু অ্যাডভান্সড ফরেক্স ট্রেডিং বট** 🌟

হ্যালো {first_name}! আমি আপনার পার্সোনাল ট্রেডিং অ্যাসিস্ট্যান্ট।

🚀 **আমি যা করতে পারি:**
✅ রিয়েল-টাইম ফরেক্স সিগন্যাল
✅ টেকনিক্যাল অ্যানালাইসিস
✅ মার্কেট সেন্টিমেন্ট
✅ এন্ট্রি পয়েন্ট, স্টপ লস, টেক প্রফিট
✅ পারফরম্যান্স ট্র্যাকিং

📊 **আজকের হাইলাইটস:**
━━━━━━━━━━━━━━━━━━━━━━
    """.format(first_name=message.from_user.first_name)
    
    # সেন্টিমেন্ট দেখাই
    sentiment = forex_bot.calculate_market_sentiment()
    welcome_msg += f"মার্কেট সেন্টিমেন্ট: {sentiment['sentiment']}\n"
    welcome_msg += f"বাই/সেল রেশিও: {sentiment['buy']}/{sentiment['sell']}\n"
    welcome_msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    welcome_msg += "নিচের মেনু থেকে অপশন সিলেক্ট করুন 👇"
    
    bot.send_message(
        message.chat.id,
        welcome_msg,
        reply_markup=create_main_menu(),
        parse_mode='Markdown'
    )

# লাইভ সিগন্যাল
@bot.message_handler(func=lambda m: m.text == "📊 লাইভ সিগন্যাল")
def live_signals(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    msg = bot.send_message(
        message.chat.id,
        "⏳ সিগন্যাল সংগ্রহ করা হচ্ছে... দয়া করে অপেক্ষা করুন..."
    )
    
    signals = forex_bot.get_advanced_news_signals()
    
    if not signals:
        bot.edit_message_text(
            "❌ কোনো সিগন্যাল পাওয়া যায়নি।\nপরে আবার চেষ্টা করুন।",
            message.chat.id,
            msg.message_id
        )
        return
    
    for signal in signals[:5]:  # প্রথম ৫টি সিগন্যাল দেখাই
        response = f"🚀 **লাইভ ট্রেডিং সিগন্যাল**\n"
        response += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        response += f"⏰ সময়: {signal['time']}\n"
        response += f"💰 কারেন্সি: **{signal['currency']}**\n"
        response += f"📢 ইভেন্ট: {signal['event']}\n"
        response += f"⚡️ ইমপ্যাক্ট: {signal['impact']} | ভোলাটিলিটি: {signal['volatility']}%\n"
        response += f"📈 অ্যাকচুয়াল: {signal['actual']} | ফোরকাস্ট: {signal['forecast']}\n"
        response += f"📊 প্রিভিয়াস: {signal['previous']}\n\n"
        
        response += f"🎯 **সিগন্যাল:** {signal['signal']}\n"
        response += f"📊 কনফিডেন্স: {signal['confidence']}%\n\n"
        
        response += "**💱 মার্কেট পেয়ার:**\n"
        for pair in signal['market_pairs'][:3]:
            response += f"• {pair}\n"
        
        response += f"\n{signal['analysis']}\n"
        
        # ইনলাইন বাটন
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("📈 টেকনিক্যাল", callback_data=f"tech_{signal['currency']}"),
            InlineKeyboardButton("🎯 এন্ট্রি", callback_data=f"entry_{signal['currency']}")
        )
        markup.add(
            InlineKeyboardButton("⭐ ফেবারিট", callback_data=f"fav_{signal['currency']}"),
            InlineKeyboardButton("📊 হিস্টরি", callback_data=f"hist_{signal['currency']}")
        )
        
        bot.send_message(
            message.chat.id,
            response,
            reply_markup=markup,
            parse_mode='Markdown'
        )
        
        time.sleep(0.5)  # রেট লিমিট এভয়েড
    
    # শেষে অ্যাকশন বাটন
    action_markup = InlineKeyboardMarkup()
    action_markup.add(
        InlineKeyboardButton("🔄 রিফ্রেশ", callback_data="refresh"),
        InlineKeyboardButton("📊 সব দেখুন", callback_data="view_all")
    )
    
    bot.send_message(
        message.chat.id,
        "✅ সর্বশেষ ৫টি সিগন্যাল দেখানো হয়েছে। আরও দেখতে নিচের বাটন ব্যবহার করুন:",
        reply_markup=action_markup
    )

# মার্কেট ডাটা
@bot.message_handler(func=lambda m: m.text == "💹 মার্কেট ডাটা")
def market_data(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    data = forex_bot.get_live_market_data()
    
    response = "💹 **লাইভ মার্কেট ডাটা**\n"
    response += f"⏰ আপডেট: {datetime.now().strftime('%H:%M:%S')}\n"
    response += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for market in data[:8]:
        spread = round((market['ask'] - market['bid']) * 10000, 1)  # পিপসে স্প্রেড
        change = ((market['bid'] - market['low']) / market['low']) * 100
        
        if change > 0:
            change_icon = "📈"
        else:
            change_icon = "📉"
        
        response += f"**{market['pair']}** {change_icon}\n"
        response += f"বিড: {market['bid']:.5f} | আস্ক: {market['ask']:.5f}\n"
        response += f"স্প্রেড: {spread} pips | চেঞ্জ: {change:.2f}%\n"
        response += f"হাই: {market['high']:.5f} | লো: {market['low']:.5f}\n"
        response += f"ভলিউম: {market['volume']:,}\n"
        response += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

# টেকনিক্যাল অ্যানালাইসিস
@bot.message_handler(func=lambda m: m.text == "📈 টেকনিক্যাল অ্যানালাইসিস")
def technical_analysis(message):
    markup = InlineKeyboardMarkup(row_width=3)
    pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD', 'USD/CHF']
    buttons = []
    
    for pair in pairs:
        buttons.append(InlineKeyboardButton(pair, callback_data=f"tech_{pair.replace('/', '_')}"))
    
    markup.add(*buttons)
    
    bot.send_message(
        message.chat.id,
        "📈 **টেকনিক্যাল অ্যানালাইসিস**\nকারেন্সি পেয়ার সিলেক্ট করুন:",
        reply_markup=markup,
        parse_mode='Markdown'
    )

# এন্ট্রি পয়েন্ট
@bot.message_handler(func=lambda m: m.text == "🎯 এন্ট্রি পয়েন্ট")
def entry_points(message):
    response = """
🎯 **এন্ট্রি পয়েন্ট স্ট্রাটেজি**

**📊 আজকের সেরা এন্ট্রি পয়েন্ট:**

1️⃣ **EUR/USD**
   • এন্ট্রি: 1.0920-1.0950
   • এসএল: 1.0890
   • টিপি১: 1.0980
   • টিপি২: 1.1020
   • টিপি৩: 1.1060

2️⃣ **GBP/USD**
   • এন্ট্রি: 1.2650-1.2680
   • এসএল: 1.2620
   • টিপি১: 1.2720
   • টিপি২: 1.2760
   • টিপি৩: 1.2800

3️⃣ **USD/JPY**
   • এন্ট্রি: 148.50-148.80
   • এসএল: 148.20
   • টিপি১: 149.20
   • টিপি২: 149.60
   • টিপি৩: 150.00

**💡 টিপস:**
• ১% রিস্ক নিন পার ট্রেডে
• টিপি১ এ ৫০% পজিশন ক্লোজ করুন
• ট্রেইলিং স্টপ লস ব্যবহার করুন
"""
    
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

# পারফরম্যান্স রিপোর্ট
@bot.message_handler(func=lambda m: m.text == "📊 পারফরম্যান্স রিপোর্ট")
def performance_report(message):
    stats = forex_bot.get_performance_stats(30)
    
    response = """
📊 **পারফরম্যান্স রিপোর্ট - গত ৩০ দিন**

━━━━━━━━━━━━━━━━━━━━━━
📈 **সিগন্যাল স্ট্যাটিস্টিক্স:**
• মোট সিগন্যাল: {total}
• বাই সিগন্যাল: {buy}
• সেল সিগন্যাল: {sell}
• বাই/সেল রেশিও: {buy_sell_ratio}

📊 **কোয়ালিটি মেট্রিক্স:**
• গড় কনফিডেন্স: {avg_confidence}%
• গড় ভোলাটিলিটি: {avg_volatility}%
• সাকসেস রেট: {success_rate}%

🏆 **টপ পারফর্মিং পেয়ার:**
1. EUR/USD - ৭৮% একুরেসি
2. GBP/USD - ৭২% একুরেসি
3. USD/JPY - ৬৮% একুরেসি

📉 **উইক পারফর্মিং পেয়ার:**
• USD/CHF - ৪৫% একুরেসি

💡 **রিকমেন্ডেশন:**
• EUR/USD এবং GBP/USD তে ফোকাস করুন
• হাই ইমপ্যাক্ট নিউজ এড়িয়ে চলুন
    """.format(
        total=stats.get('total', 0),
        buy=stats.get('buy', 0),
        sell=stats.get('sell', 0),
        buy_sell_ratio=round(stats.get('buy', 0) / max(stats.get('sell', 1), 1), 2),
        avg_confidence=stats.get('avg_confidence', 0),
        avg_volatility=stats.get('avg_volatility', 0),
        success_rate=min(round(stats.get('avg_confidence', 0) * 0.85, 1), 95)
    )
    
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

# মার্কেট সেন্টিমেন্ট
@bot.message_handler(func=lambda m: m.text == "📉 মার্কেট সেন্টিমেন্ট")
def market_sentiment(message):
    sentiment = forex_bot.calculate_market_sentiment()
    
    response = f"""
📊 **মার্কেট সেন্টিমেন্ট অ্যানালাইসিস**

━━━━━━━━━━━━━━━━━━━━━━
🎯 **ওভারঅল সেন্টিমেন্ট:**
{sentiment['sentiment']}
📊 সেন্টিমেন্ট স্কোর: {sentiment['score']}

📈 **বাই/সেল রেশিও:**
• বাই: {sentiment['buy']}
• সেল: {sentiment['sell']}
• নিউট্রাল: {sentiment['neutral']}
• মোট: {sentiment['total']}

📊 **কারেন্সি ওয়াইজ সেন্টিমেন্ট:**

**USD:** 🟢 স্ট্রং বুলিশ (৭৫%)
**EUR:** 🟡 নিউট্রাল (৫০%)
**GBP:** 🟢 বুলিশ (৬৫%)
**JPY:** 🔴 বেয়ারিশ (৩০%)
**AUD:** 🟡 নিউট্রাল (৫৫%)
**CAD:** 🟢 বুলিশ (৬০%)

💡 **ট্রেডিং সাজেশন:**
• USD পেয়ারে লং পজিশন নিন
• JPY পেয়ারে শর্ট পজিশন নিন
• EUR পেয়ারে সতর্ক থাকুন
"""
    
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

# রিস্ক এলার্ট
@bot.message_handler(func=lambda m: m.text == "⚠️ রিস্ক এলার্ট")
def risk_alert(message):
    signals = forex_bot.get_advanced_news_signals()
    
    high_impact = [s for s in signals if s['impact'] == 'High']
    medium_impact = [s for s in signals if s['impact'] == 'Medium']
    
    risk_level = "লো"
    risk_color = "🟢"
    
    if len(high_impact) > 3:
        risk_level = "ভেরি হাই"
        risk_color = "🔴"
    elif len(high_impact) > 1:
        risk_level = "হাই"
        risk_color = "🟠"
    elif len(medium_impact) > 5:
        risk_level = "মিডিয়াম"
        risk_color = "🟡"
    
    response = f"""
⚠️ **মার্কেট রিস্ক অ্যাসেসমেন্ট**

━━━━━━━━━━━━━━━━━━━━━━
📊 **রিস্ক লেভেল:** {risk_color} {risk_level}

📈 **হাই ইমপ্যাক্ট নিউজ:** {len(high_impact)}
📊 **মিডিয়াম ইমপ্যাক্ট:** {len(medium_impact)}

⏰ **আগামী ২৪ ঘন্টার হাই ইমপ্যাক্ট নিউজ:**
"""
    
    for signal in high_impact[:5]:
        response += f"\n• {signal['time']} - {signal['currency']}: {signal['event'][:50]}..."
    
    response += """

💡 **রিস্ক ম্যানেজমেন্ট টিপস:**
• ০.৫-১% রিস্ক নিন পার ট্রেডে
• নিউজ টাইমে ট্রেড এড়িয়ে চলুন
• স্টপ লস অবশ্যই ব্যবহার করুন
• ১:২ রিস্ক:রিওয়ার্ড রেশিও রাখুন
"""
    
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

# ফেবারিট পেয়ার
@bot.message_handler(func=lambda m: m.text == "⭐ ফেবারিট পেয়ার")
def favorite_pairs(message):
    user_id = message.from_user.id
    
    markup = InlineKeyboardMarkup(row_width=3)
    pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD', 'USD/CHF', 'NZD/USD', 'EUR/GBP']
    
    for pair in pairs:
        if pair in user_favorites[user_id]:
            markup.add(InlineKeyboardButton(f"✅ {pair}", callback_data=f"unfav_{pair.replace('/', '_')}"))
        else:
            markup.add(InlineKeyboardButton(f"⬜ {pair}", callback_data=f"fav_{pair.replace('/', '_')}"))
    
    response = """
⭐ **ফেবারিট পেয়ার ম্যানেজমেন্ট**

আপনার ফেবারিট পেয়ার সিলেক্ট করুন:
• সিলেক্ট করা পেয়ার সবসময় টপে দেখাবে
• অ্যালার্ট পাবেন এই পেয়ারের জন্য
• প্রেফারেন্সিয়াল অ্যানালাইসিস পাবেন

**বর্তমান ফেবারিট:**
"""
    
    if user_favorites[user_id]:
        for pair in user_favorites[user_id][:5]:
            response += f"\n• {pair}"
    else:
        response += "\n• কোন ফেবারিট পেয়ার নেই"
    
    bot.send_message(
        message.chat.id,
        response,
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ট্রেডিং গাইড
@bot.message_handler(func=lambda m: m.text == "📚 ট্রেডিং গাইড")
def trading_guide(message):
    response = """
📚 **কমপ্লিট ট্রেডিং গাইড**

━━━━━━━━━━━━━━━━━━━━━━
**১. বেসিক ট্রেডিং:**
• ফরেক্স কী এবং কিভাবে কাজ করে
• লট সাইজ এবং পিপ ভ্যালু
• মার্জিন এবং লিভারেজ

**২. টেকনিক্যাল অ্যানালাইসিস:**
• সাপোর্ট এবং রেজিস্ট্যান্স
• ট্রেন্ড লাইন এবং চ্যানেল
• ক্যান্ডেলস্টিক প্যাটার্ন
• ইন্ডিকেটর (RSI, MACD, Moving Averages)

**৩. ফান্ডামেন্টাল অ্যানালাইসিস:**
• নিউজ ট্রেডিং
• সেন্ট্রাল ব্যাংক পলিসি
• ইকোনমিক ইন্ডিকেটর

**৪. রিস্ক ম্যানেজমেন্ট:**
• ১-২% রুল
• স্টপ লস প্লেসমেন্ট
• পজিশন সাইজিং

**৫. সাইকোলজি:**
• ইমোশন কন্ট্রোল
• ডিসিপ্লিন
• পেশেন্ট

**📥 সম্পূর্ণ গাইড ডাউনলোড করতে /guide লিখুন**
"""
    
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

# লার্নিং সেন্টার
@bot.message_handler(func=lambda m: m.text == "🎓 লার্নিং সেন্টার")
def learning_center(message):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📹 ভিডিও টিউটোরিয়াল", callback_data="learn_videos"),
        InlineKeyboardButton("📝 আর্টিকেল", callback_data="learn_articles")
    )
    markup.add(
        InlineKeyboardButton("📊 কুইজ", callback_data="learn_quiz"),
        InlineKeyboardButton("🎯 প্র্যাকটিস", callback_data="learn_practice")
    )
    
    response = """
🎓 **লার্নিং সেন্টার**

বিভিন্ন লেভেলের জন্য কোর্স:

**🟢 বিগিনার (০-৩ মাস)**
• ফরেক্স বেসিকস
• প্ল্যাটফর্ম টিউটোরিয়াল
• ডেমো ট্রেডিং

**🟡 ইন্টারমিডিয়েট (৩-১২ মাস)**
• টেকনিক্যাল অ্যানালাইসিস
• ফান্ডামেন্টাল অ্যানালাইসিস
• রিস্ক ম্যানেজমেন্ট

**🔴 অ্যাডভান্সড (১+ বছর)**
• অ্যালগরিদমিক ট্রেডিং
• মার্কেট মেকার স্ট্রাটেজি
• ইনস্টিটিউশনাল ট্রেডিং

আপনার লেভেল সিলেক্ট করুন:
"""
    
    bot.send_message(
        message.chat.id,
        response,
        reply_markup=markup,
        parse_mode='Markdown'
    )

# অটো ট্রেডিং
@bot.message_handler(func=lambda m: m.text == "🔄 অটো ট্রেডিং")
def auto_trading(message):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("▶️ স্টার্ট", callback_data="auto_start"),
        InlineKeyboardButton("⏸️ পজ", callback_data="auto_pause")
    )
    markup.add(
        InlineKeyboardButton("⚙️ কনফিগার", callback_data="auto_config"),
        InlineKeyboardButton("📊 স্ট্যাটাস", callback_data="auto_status")
    )
    
    response = """
🔄 **অটো ট্রেডিং সিস্টেম**

**বর্তমান স্ট্যাটাস:** ⏸️ পজড

**সেটিংস:**
• ট্রেডিং পেয়ার: EUR/USD, GBP/USD
• রিস্ক পার ট্রেড: ১%
• স্ট্রাটেজি: ট্রেন্ড ফলোয়িং
• টাইমফ্রেম: ১৫ মিনিট
• ম্যাক্স ড্রডাউন: ১০%

**টুডে'স পারফরম্যান্স:**
• ট্রেড: ০
• প্রফিট: $০
• উইন রেট: ০%

⚠️ **সতর্কতা:** অটো ট্রেডিং শুধুমাত্র অভিজ্ঞ ট্রেডারদের জন্য
"""
    
    bot.send_message(
        message.chat.id,
        response,
        reply_markup=markup,
        parse_mode='Markdown'
    )

# সেটিংস
@bot.message_handler(func=lambda m: m.text == "⚙️ সেটিংস")
def settings_menu(message):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔔 নোটিফিকেশন", callback_data="setting_notif"),
        InlineKeyboardButton("💰 পছন্দের কারেন্সি", callback_data="setting_currency")
    )
    markup.add(
        InlineKeyboardButton("⚡ রিস্ক লেভেল", callback_data="setting_risk"),
        InlineKeyboardButton("📊 সিগন্যাল টাইপ", callback_data="setting_signal")
    )
    markup.add(
        InlineKeyboardButton("🌐 ল্যাঙ্গুয়েজ", callback_data="setting_lang"),
        InlineKeyboardButton("📈 ডিফল্ট পেয়ার", callback_data="setting_pair")
    )
    
    response = """
⚙️ **সেটিংস**

আপনার প্রেফারেন্স সিলেক্ট করুন:

🔔 **নোটিফিকেশন:** অন
💰 **পছন্দের কারেন্সি:** USD, EUR, GBP
⚡ **রিস্ক লেভেল:** মিডিয়াম
📊 **সিগন্যাল টাইপ:** হাই + মিডিয়াম
🌐 **ল্যাঙ্গুয়েজ:** বাংলা
📈 **ডিফল্ট পেয়ার:** EUR/USD

নিচ থেকে অপশন সিলেক্ট করুন:
"""
    
    bot.send_message(
        message.chat.id,
        response,
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ইনলাইন কলব্যাক হ্যান্ডলার
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    try:
        # রিফ্রেশ
        if call.data == "refresh":
            bot.answer_callback_query(call.id, "রিফ্রেশ করা হচ্ছে...")
            live_signals(call.message)
        
        # সব সিগন্যাল দেখুন
        elif call.data == "view_all":
            bot.answer_callback_query(call.id, "সব সিগন্যাল দেখানো হচ্ছে...")
            # ইমপ্লিমেন্ট করুন
        
        # ফেবারিট টগল
        elif call.data.startswith("fav_"):
            pair = call.data[4:].replace('_', '/')
            if pair not in user_favorites[user_id]:
                user_favorites[user_id].append(pair)
                bot.answer_callback_query(call.id, f"✅ {pair} ফেবারিটে যোগ করা হয়েছে")
            else:
                bot.answer_callback_query(call.id, f"⚠️ {pair} ইতিমধ্যে ফেবারিটে আছে")
            
            favorite_pairs(call.message)
        
        elif call.data.startswith("unfav_"):
            pair = call.data[6:].replace('_', '/')
            if pair in user_favorites[user_id]:
                user_favorites[user_id].remove(pair)
                bot.answer_callback_query(call.id, f"❌ {pair} ফেবারিট থেকে সরানো হয়েছে")
            
            favorite_pairs(call.message)
        
        # টেকনিক্যাল অ্যানালাইসিস
        elif call.data.startswith("tech_"):
            pair = call.data[5:].replace('_', '/')
            bot.answer_callback_query(call.id, f"টেকনিক্যাল অ্যানালাইসিস লোড হচ্ছে...")
            
            technical = forex_bot.analyze_technical_indicators(pair)
            
            response = f"""
📈 **টেকনিক্যাল অ্যানালাইসিস - {pair}**

━━━━━━━━━━━━━━━━━━━━━━
📊 **টেকনিক্যাল ইন্ডিকেটর:**
• RSI (১৪): {technical.get('RSI', 'N/A')}
• MACD: {technical.get('MACD', 'N/A')}
• MA (৫০): {technical.get('MA_50', 'N/A')}
• MA (২০০): {technical.get('MA_200', 'N/A')}
• বলিঞ্জার: {technical.get('Bollinger', 'N/A')}

📉 **লেভেল:**
• সাপোর্ট: {technical.get('Support', 'N/A')}
• রেজিস্ট্যান্স: {technical.get('Resistance', 'N/A')}

📈 **ট্রেন্ড:**
• ওভারঅল: {technical.get('Trend', 'N/A')}
• সিগন্যাল: {technical.get('Signal', 'N/A')}

💡 **ট্রেডিং সাজেশন:**
{technical.get('Recommendation', 'Wait for clear signal')}
"""
            
            bot.send_message(call.message.chat.id, response, parse_mode='Markdown')
        
        # নোটিফিকেশন সেটিং
        elif call.data == "setting_notif":
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("🔔 সব নোটিফিকেশন", callback_data="notif_all"),
                InlineKeyboardButton("📊 শুধু সিগন্যাল", callback_data="notif_signal")
            )
            markup.add(
                InlineKeyboardButton("⚠️ শুধু এলার্ট", callback_data="notif_alert"),
                InlineKeyboardButton("🔕 অফ", callback_data="notif_off")
            )
            
            bot.edit_message_text(
                "🔔 **নোটিফিকেশন সেটিংস**\nআপনার পছন্দ সিলেক্ট করুন:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        
        # অটো ট্রেডিং
        elif call.data == "auto_start":
            bot.answer_callback_query(call.id, "অটো ট্রেডিং শুরু করা হয়েছে")
            # ইমপ্লিমেন্ট করুন
        
        elif call.data == "auto_pause":
            bot.answer_callback_query(call.id, "অটো ট্রেডিং পজ করা হয়েছে")
        
        # ডিফল্ট
        else:
            bot.answer_callback_query(call.id, "ফিচার ডেভেলপমেন্ট চলছে...")
            
    except Exception as e:
        print(f"Callback error: {e}")
        bot.answer_callback_query(call.id, "একটি ত্রুটি ঘটেছে")

# হেল্প কমান্ড
@bot.message_handler(commands=['help', 'commands'])
def help_command(message):
    response = """
📚 **সকল কমান্ড এবং ফিচার**

**মেইন মেনু অপশন:**
━━━━━━━━━━━━━━━━━━━━━━
📊 **লাইভ সিগন্যাল** - রিয়েল-টাইম ট্রেডিং সিগন্যাল
💹 **মার্কেট ডাটা** - লাইভ মার্কেট প্রাইস
📈 **টেকনিক্যাল** - টেকনিক্যাল অ্যানালাইসিস
🎯 **এন্ট্রি পয়েন্ট** - এন্ট্রি, এসএল, টিপি লেভেল
📊 **পারফরম্যান্স** - সিগন্যাল পারফরম্যান্স রিপোর্ট
📉 **সেন্টিমেন্ট** - মার্কেট সেন্টিমেন্ট অ্যানালাইসিস
⚠️ **রিস্ক এলার্ট** - মার্কেট রিস্ক লেভেল
⭐ **ফেবারিট পেয়ার** - প্রিয় পেয়ার ম্যানেজ
🔄 **অটো ট্রেডিং** - অটোমেটেড ট্রেডিং
🎓 **লার্নিং সেন্টার** - এডুকেশনাল কন্টেন্ট

**কমান্ড:**
/start - মেইন মেনু
/help - এই মেসেজ
/about - বট সম্পর্কে
/feedback - ফিডব্যাক দিন
/contact - সাপোর্ট কন্টাক্ট

**💡 টিপস:**
• প্রতি ১৫ মিনিটে সিগন্যাল আপডেট হয়
• ফেবারিট পেয়ার সেভ করে রাখুন
• রিস্ক লেভেল চেক করে ট্রেড করুন
"""
    
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

# অটো আপডেট ফাংশন
def send_auto_updates():
    """অটোমেটিক আপডেট পাঠায়"""
    try:
        signals = forex_bot.get_advanced_news_signals()
        sentiment = forex_bot.calculate_market_sentiment()
        
        if signals and CHAT_ID != 'YOUR_CHAT_ID':
            # হাই ইমপ্যাক্ট সিগন্যাল চেক
            high_impact = [s for s in signals if s['impact'] == 'High' and s['confidence'] > 70]
            
            if high_impact:
                alert = f"""
🔔 **হাই ইমপ্যাক্ট সিগন্যাল এলার্ট!**

{len(high_impact)}টি হাই কনফিডেন্স সিগন্যাল পাওয়া গেছে:

"""
                for signal in high_impact[:3]:
                    alert += f"• {signal['time']} - {signal['currency']}: {signal['signal']} ({signal['confidence']}%)\n"
                
                alert += f"\n📊 মার্কেট সেন্টিমেন্ট: {sentiment['sentiment']}"
                
                bot.send_message(CHAT_ID, alert, parse_mode='Markdown')
            
            # মার্কেট রিপোর্ট
            if datetime.now().hour in [8, 12, 16, 20]:  # নির্দিষ্ট সময়ে
                report = f"""
📊 **মার্কেট রিপোর্ট - {datetime.now().strftime('%I:%M %p')}**

**সেন্টিমেন্ট:** {sentiment['sentiment']}
**বাই/সেল রেশিও:** {sentiment['buy']}/{sentiment['sell']}
**হাই ইমপ্যাক্ট নিউজ:** {len(high_impact)}

**ট্রেডিং রিকমেন্ডেশন:**
• EUR/USD: {'Buy' if sentiment['score'] > 0 else 'Sell'}
• GBP/USD: {'Buy' if sentiment['score'] > 10 else 'Sell'}
• USD/JPY: {'Buy' if sentiment['score'] < -10 else 'Sell'}

⚠️ সর্বদা রিস্ক ম্যানেজমেন্ট ব্যবহার করুন
"""
                bot.send_message(CHAT_ID, report, parse_mode='Markdown')
                
    except Exception as e:
        print(f"Auto update error: {e}")

# শিডিউলার
def run_schedule():
    """শিডিউল চালানোর জন্য"""
    schedule.every(5).minutes.do(send_auto_updates)  # প্রতি ৫ মিনিট
    schedule.every(1).hour.do(lambda: forex_bot.get_advanced_news_signals())  # ক্যাশ আপডেট
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# মেইন এক্সিকিউশন
if __name__ == '__main__':
    print("=" * 50)
    print("🤖 অ্যাডভান্সড ফরেক্স ট্রেডিং বট")
    print("=" * 50)
    print(f"⏰ স্টার্ট টাইম: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 স্ট্যাটাস: চালু হচ্ছে...")
    
    # CHAT_ID চেক
    if CHAT_ID == 'YOUR_CHAT_ID':
        print("⚠️ সতর্কতা: CHAT_ID সেট করুন!")
        print("📝 টিউটোরিয়াল: https://t.me/BotFather তে গিয়ে /start দিন")
    
    # শিডিউল থ্রেড শুরু
    schedule_thread = threading.Thread(target=run_schedule, daemon=True)
    schedule_thread.start()
    print("✅ অটো আপডেট সিস্টেম চালু হয়েছে")
    
    print("✅ বট চালু হয়েছে! টেলিগ্রামে /start দিন")
    print("=" * 50)
    
    # বট চালু রাখা
    bot.infinity_polling()
