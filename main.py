import os
import time
import asyncio
import yfinance as yf
from telegram import Bot
from datetime import datetime
import pytz

# ================= CONFIGURATION =================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

FOREX_PAIRS = [
    'DX-Y.NYB', 'EURUSD=X', 'GBPUSD=X', 'USDCHF=X', 
    'EURAUD=X', 'GBPAUD=X', 'AUDCHF=X', 'AUDUSD=X', 
    'NZDUSD=X', 'EURCAD=X', 'GBPCAD=X', 'CADCHF=X', 
    'EURJPY=X', 'GBPJPY=X', 'CHFJPY=X'
]

# Metals and Indices (Always checked)
ALWAYS_CHECK = ['XAUUSD=X', 'XAGUSD=X', 'YM=F', 'NQ=F', 'ES=F']

# Time Window (EST)
START_HOUR = 20  # 8 PM EST
END_HOUR = 11    # 11 AM EST

async def send_telegram_alert(message):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
    except Exception as e:
        print(f"Error sending message: {e}")

def check_ema_cross(pair, interval):
    try:
        # Fetch data
        period = '5d' if interval == '15m' else '2d'
        data = yf.download(pair, period=period, interval=interval, progress=False)
        
        if len(data) < 100:
            return

        # Calculate 100 EMA
        data['EMA_100'] = data['Close'].ewm(span=100, adjust=False).mean()
        
        # Candles
        prev_candle = data.iloc[-3]
        last_candle = data.iloc[-2]
        
        msg = None
        
        # Bullish Cross
        if prev_candle['Close'] < prev_candle['EMA_100'] and last_candle['Close'] > last_candle['EMA_100']:
            msg = f"🟢 <b>BUY ALERT: {pair}</b>\nTF: {interval}\nPrice broke ABOVE 100 EMA\nPrice: {last_candle['Close']:.2f}"
            
        # Bearish Cross
        elif prev_candle['Close'] > prev_candle['EMA_100'] and last_candle['Close'] < last_candle['EMA_100']:
            msg = f"🔴 <b>SELL ALERT: {pair}</b>\nTF: {interval}\nPrice broke BELOW 100 EMA\nPrice: {last_candle['Close']:.2f}"
            
        if msg:
            print(f"!!! SIGNAL: {pair} !!!")
            asyncio.run(send_telegram_alert(msg))
            
    except Exception as e:
        print(f"Error checking {pair}: {e}")

def is_trading_hours():
    est = pytz.timezone('US/Eastern')
    now = datetime.now(est)
    if START_HOUR > END_HOUR:
        return now.hour >= START_HOUR or now.hour < END_HOUR
    else:
        return START_HOUR <= now.hour < END_HOUR

def main_loop():
    print(f"✅ Bot Started in Continuous Mode at {datetime.now().strftime('%H:%M')}")
    # Send a startup message so you know it's alive
    try:
        asyncio.run(send_telegram_alert("✅ Market Scanner is Online (Continuous Loop Mode)"))
    except:
        pass

    last_checked_minute = -1

    while True:
        # Get current time
        now = datetime.now()
        current_minute = now.minute
        
        # We only run logic ONCE per minute, exactly when the minute flips
        if current_minute != last_checked_minute:
            last_checked_minute = current_minute
            print(f"⏰ Scanning Minute: {current_minute}...")

            if not is_trading_hours():
                print("💤 Outside trading hours (EST). Waiting...")
            else:
                # 1. ALWAYS Check Metals/Indices (Every 5 mins: 0, 5, 10, 15...)
                if current_minute % 5 == 0:
                    print("   > Checking Metals & Indices...")
                    for pair in ALWAYS_CHECK:
                        check_ema_cross(pair, interval='5m')

                # 2. Check Forex (Every 15 mins: 0, 15, 30, 45)
                if current_minute % 15 == 0:
                    print("   > Checking Forex...")
                    for pair in FOREX_PAIRS:
                        check_ema_cross(pair, interval='15m')
        
        # Sleep for 10 seconds to save CPU, then check time again
        time.sleep(10)

if __name__ == "__main__":
    if TELEGRAM_TOKEN and CHAT_ID:
        main_loop()
    else:
        raise ValueError("Tokens missing!")
