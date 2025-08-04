# bot.py - Enhanced version
import logging
import asyncio
from telegram.ext import (
    Application,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram.error import Conflict, NetworkError
from config import TELEGRAM_BOT_TOKEN
from handlers import (
    start,
    location,
    photo,
    description,
    description_skip,
    crash_time_delta,
    submit,
    cancel,
    review_handler,
    LOCATION,
    PHOTO,
    DESCRIPTION,
    CRASH_TIME_DELTA,
    CONFIRMATION,
)

# Enhanced logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def setup_bot():
    """Setup bot with proper timeout configuration."""
    try:
        # Create application with proper timeout settings
        application = (
            Application.builder()
            .token(TELEGRAM_BOT_TOKEN)
            .get_updates_read_timeout(30)      # Fix for deprecation warning
            .get_updates_write_timeout(30)     # Fix for deprecation warning
            .get_updates_connect_timeout(30)   # Fix for deprecation warning
            .build()
        )
        
        # Ensure no webhooks are set (force polling mode)
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Cleared any existing webhooks")
        
        return application
        
    except Exception as e:
        logger.error(f"Failed to setup bot: {e}")
        raise

def main() -> None:
    """Run the bot with proper timeout handling."""
    try:
        # Create the Application with proper timeouts
        application = asyncio.get_event_loop().run_until_complete(setup_bot())

        # Add your conversation handler (same as before)
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", start),
                MessageHandler(filters.Regex(r"^➕ New Report$"), start),
            ],
            states={
                LOCATION: [MessageHandler(filters.LOCATION, location)],
                PHOTO: [MessageHandler(filters.PHOTO, photo)],
                DESCRIPTION: [
                    MessageHandler(filters.Regex(r"(?i)^skip$"), description_skip),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, description),
                ],
                CRASH_TIME_DELTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, crash_time_delta)],
                CONFIRMATION: [
                    MessageHandler(filters.Regex(r"(?i)^Submit Report$"), submit),
                    MessageHandler(filters.Regex(r"(?i)^Cancel$"), cancel),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            per_message=False
        )

        application.add_handler(conv_handler)
        application.add_handler(CallbackQueryHandler(review_handler))

        logger.info("Starting bot with enhanced error handling...")
        
        # Simplified run_polling (no deprecated timeout parameters)
        application.run_polling(
            poll_interval=2.0,
            bootstrap_retries=3,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Bot startup failed: {e}")
        raise
    finally:
        logger.info("Bot stopped.")

if __name__ == "__main__":
    main()
