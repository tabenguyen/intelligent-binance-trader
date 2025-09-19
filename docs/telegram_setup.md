# Telegram Notifications Setup

This guide helps you set up Telegram notifications for your trading bot.

## Step 1: Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a chat with BotFather and send `/newbot`
3. Follow the instructions to create your bot:
   - Choose a name for your bot (e.g., "My Trading Bot")
   - Choose a username (must end with 'bot', e.g., "my_trading_bot")
4. BotFather will give you a **Bot Token** - save this securely!

## Step 2: Get Your Chat ID

### Method 1: Using userinfobot

1. Search for `@userinfobot` in Telegram
2. Start a chat and send any message
3. The bot will reply with your user information including your **Chat ID**

### Method 2: Using your bot

1. Start a chat with your newly created bot
2. Send any message to your bot
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for the `chat.id` field in the response

### Method 3: For group chats

1. Add your bot to the group
2. Send a message in the group
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for the `chat.id` field (will be negative for groups)

## Step 3: Configure Environment Variables

Add these environment variables to your `.env` file:

```bash
# Telegram Notifications
ENABLE_TELEGRAM_NOTIFICATIONS=true
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

## Step 4: Test Your Setup

Run your trading bot and you should see:

- A test message when the bot starts
- Trading signals sent to your Telegram chat
- Trade completion notifications
- Error notifications

## Features

The Telegram notification service provides:

### 📡 **Signal Notifications**

- Symbol and strategy information
- Entry price and confidence level
- Stop loss and take profit levels
- Core conditions status

### 📈 **Trade Notifications**

- Trade completion status
- Entry and exit prices
- Profit/Loss calculations
- Trade duration

### 🚨 **Error Notifications**

- Critical trading errors
- System issues
- API failures

### 🔄 **Fallback Support**

- If Telegram fails, notifications fall back to logging
- Dual notification system (both Telegram and logs)

## Message Format

Messages are formatted using Telegram's HTML markup:

- **Bold text** for important information
- `Code blocks` for prices and technical data
- 📊 Emojis for visual clarity

## Troubleshooting

### Bot Token Issues

- Ensure your bot token is correct and active
- Check that you haven't revoked the bot token

### Chat ID Issues

- Verify your chat ID is correct
- For groups, ensure the bot is added and has permission to send messages
- Chat IDs for groups are negative numbers

### Network Issues

- Check your internet connection
- Verify Telegram API is accessible from your server
- Check firewall settings if running on a server

### Permissions

- Ensure your bot can send messages to the chat
- For groups, the bot needs proper permissions

## Security Notes

- Keep your bot token secure and never share it publicly
- Use environment variables, never hardcode tokens in your code
- Consider using a dedicated chat/channel for trading notifications
- Regularly monitor who has access to your notification channels

## Advanced Usage

### Multiple Chat IDs

Currently supports one chat ID. For multiple recipients, you can:

1. Create a group and add all recipients
2. Use the group chat ID
3. Or modify the code to support multiple chat IDs

### Custom Message Formatting

You can customize message formats by modifying the `TelegramNotificationService` class in:
`src/services/notification_service.py`

### Rate Limiting

Telegram has rate limits (30 messages per second). The current implementation handles single notifications well, but for high-frequency trading, consider implementing rate limiting.
