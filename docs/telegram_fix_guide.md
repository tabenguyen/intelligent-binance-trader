# Telegram Notification Setup Guide

## 🚨 Current Issue: "Bad Request: chat not found"

Your Telegram bot is configured but the **chat ID is incorrect**. Here's how to fix it:

## ✅ Step-by-Step Fix

### 1. Start a Chat with Your Bot

1. Open Telegram and search for `@ema_26_bot`
2. Click on the bot and press **"START"**
3. Send any message like `/start` or `hello`

### 2. Get Your Correct Chat ID

Run this command to get your actual chat ID:

```bash
cd /home/tam/Workspaces/trading-bot-ai
python3 -c "
import requests
import os
from dotenv import load_dotenv
load_dotenv('.env')

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
response = requests.get(f'https://api.telegram.org/bot{bot_token}/getUpdates')
updates = response.json()

if updates['ok'] and updates['result']:
    for update in updates['result'][-3:]:
        if 'message' in update:
            chat = update['message']['chat']
            print(f'Chat ID: {chat[\"id\"]} | Name: {chat.get(\"first_name\", \"N/A\")}')
else:
    print('No messages found. Make sure you sent /start to the bot!')
"
```

### 3. Update Your .env File

Replace the chat ID in your `.env` file:

```bash
# Current (incorrect):
TELEGRAM_CHAT_ID=1052898239

# Replace with the correct Chat ID from step 2:
TELEGRAM_CHAT_ID=YOUR_ACTUAL_CHAT_ID
```

### 4. Test the Configuration

```bash
cd /home/tam/Workspaces/trading-bot-ai
python3 test_telegram.py
```

## 🔧 Alternative: Disable Telegram Temporarily

If you want to continue without Telegram notifications:

```bash
# Edit .env file and set:
ENABLE_TELEGRAM_NOTIFICATIONS=false
```

## 📱 Expected Telegram Notifications

Once fixed, you'll receive messages like:

```
✅ Trade Completed: SXTUSDT
📊 Direction: BUY
🔢 Quantity: 189.610200
📈 Entry: $0.08
📉 Exit: $0.08
📈 P&L: $0.99
⏱ Duration: 13.3d
```

## 🚀 Current Status

- ✅ **Bot Token**: Valid (`@ema_26_bot` is working)
- ❌ **Chat ID**: Incorrect (needs to be updated)
- ✅ **Error Handling**: Improved (won't crash the bot)
- ✅ **Position Updates**: Working correctly without Telegram

Your trading bot will continue to work normally even with Telegram misconfigured. All notifications still go to log files.
