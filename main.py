import os
import yfinance as yf
import pandas as pd
import asyncio
from telegram import Bot
from datetime import datetime
import pytz

# ================= CONFIGURATION =================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# List 1: Forex Pairs (15m Timeframe)
FOREX_PAIRS = [
    'DX-Y.NYB', 'EURUSD=X', 'GBPUSD=X', 'USDCHF=X', 
    'EURAUD=X', 'GBPAUD=X', 'AUDCHF=X', 'AUDUSD=X', 
    'NZDUSD=X', 'EURCAD=X', 'GBPCAD=X', 'CADCHF=X', 
    'EURJPY=X', 'GBPJPY=X', 'CHFJPY=X'
]

# List 2: Metal Pairs (5m Timeframe - Always Checked)
METAL_PAIRS = ['XAUUSD=X', 'XAGUSD=X']

# List 3: Indices Pairs (5m Timeframe - Always Checked)
# Uses Futures tickers for best live data accuracy
INDICES_PAIRS = ['YM=F', 'NQ=F', 'ES=F']

# Time Window (EST)
START_HOUR = 20  # 8 PM EST
END_HOUR = 11    # 11 AM EST

# ================= LOGIC =================

def is_in_time_window():
    est = pytz.timezone('US/Eastern')
    now = datetime.now(est)
    
    # Logic for window crossing midnight
    if START_HOUR > END_HOUR:
        return now.hour >= START_HOUR or now.hour < END_HOUR
    else:
        return START_HOUR <= now.hour < END_HOUR

async def send_telegram_alert(message):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
    except Exception as e:
        print(f"Error sending message: {e}")

def calculate_ema_cross(pair, interval):
    try:
        # Fetch data: 5d for 15m, 2d for 5m
        period = '5d' if interval == '15m' else '2d'
        data = yf.download(pair, period=period, interval=interval, progress=False)
        
        if len(data) < 100:
            return

        # Calculate 100 EMA
        data['EMA_100'] = data['Close'].ewm(span=100, adjust=False).mean()
        
        # Get candles (Index -2 is last CLOSED candle)
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
            print(f"!!! SIGNAL FOUND: {pair} !!!")
            asyncio.run(send_telegram_alert(msg))
            
    except Exception as e:
        print(f"Error checking {pair}: {e}")

def run_scanner():
    if not is_in_time_window():
        print("Outside trading hours. Exiting...")
        return

    current_minute = datetime.now().minute
    print(f"Scanning market... Minute: {current_minute}")

    # 1. ALWAYS check Metals AND Indices (Every 5 mins)
    # We combine both lists here
    for pair in METAL_PAIRS + INDICES_PAIRS:
        calculate_ema_cross(pair, interval='5m')

    # 2. Check Forex (Only around :00, :15, :30, :45)
    # Using < 10 to handle GitHub delays
    if current_minute % 15 < 10: 
        print("Checking Forex (15m)...")
        for pair in FOREX_PAIRS:
            calculate_ema_cross(pair, interval='15m')
    else:
        print(f"Skipping Forex check (Minute {current_minute} not in window)")

if __name__ == "__main__":
    if TELEGRAM_TOKEN and CHAT_ID:
        run_scanner()
    else:
        raise ValueError("Telegram tokens not found! Check Repository Secrets.")
