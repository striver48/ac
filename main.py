# ORIGINAL CODE (COMMENTED OUT):
        # if prev_candle['Close'] < prev_candle['EMA_100'] and last_candle['Close'] > last_candle['EMA_100']:
        
        # --- TEST CODE: FORCE ALERT ---
        # Trigger alert if price is simply above 0 (Always True)
        if last_candle['Close'] > 0:
             msg = f"🔔 TEST ALERT: {pair} is working!\nPrice: {last_candle['Close']:.2f}"
             asyncio.run(send_telegram_alert(msg))
             # Sleep for 1 second to avoid hitting Telegram limits too fast
             import time
             time.sleep(1)
             return # Stop after one alert per pair so we don't send double
        # -----------------------------
