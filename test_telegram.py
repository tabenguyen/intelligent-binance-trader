#!/usr/bin/env python3
"""
Test script to verify Telegram bot configuration and connection.
"""
import requests
import os
from src.utils.env_loader import load_environment

def test_telegram_bot():
    """Test Telegram bot configuration."""
    
    # Load environment variables
    load_environment()
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    print("=== Telegram Bot Configuration Test ===")
    print(f"Bot Token: {'✅ Set' if bot_token else '❌ Missing'}")
    print(f"Chat ID: {'✅ Set' if chat_id else '❌ Missing'}")
    
    if not bot_token or not chat_id:
        print("\n❌ Configuration incomplete. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file")
        return False
    
    # Test bot info
    print(f"\nBot Token (first 10 chars): {bot_token[:10]}...")
    print(f"Chat ID: {chat_id}")
    
    # Test getMe endpoint
    print("\n=== Testing Bot Info ===")
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info['ok']:
                print(f"✅ Bot Info: @{bot_info['result']['username']} ({bot_info['result']['first_name']})")
            else:
                print(f"❌ Bot API Error: {bot_info}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False
    
    # Test sending a message
    print("\n=== Testing Message Send ===")
    try:
        test_message = "🧪 <b>Telegram Test Message</b>\n✅ Your trading bot can send notifications!"
        
        payload = {
            'chat_id': chat_id,
            'text': test_message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        response = requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", 
                               json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result['ok']:
                print("✅ Test message sent successfully!")
                return True
            else:
                print(f"❌ Message Send Error: {result}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"❌ Error Details: {error_data.get('description', 'Unknown error')}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"❌ Send Error: {e}")
        return False

if __name__ == "__main__":
    success = test_telegram_bot()
    print(f"\n{'=' * 50}")
    print(f"Overall Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    if not success:
        print("\nTroubleshooting Tips:")
        print("1. Verify bot token is correct")
        print("2. Make sure you've started a chat with the bot (@YourBotName)")
        print("3. Check that chat_id is correct (try sending /start to the bot)")
        print("4. Ensure bot has permission to send messages")