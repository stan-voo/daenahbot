# webhook_cleanup.py - Run this once to clear webhooks
import asyncio
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN

async def clear_webhook():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        # Delete any existing webhook
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook cleared successfully")
        
        # Get current webhook info to verify
        webhook_info = await bot.get_webhook_info()
        print(f"Current webhook URL: {webhook_info.url}")
        print(f"Pending updates: {webhook_info.pending_update_count}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(clear_webhook())