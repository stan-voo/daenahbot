# bot.py - Simplified version after Railway teardown fix
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
    odeme_command,
    LOCATION,
    PHOTO,
    DESCRIPTION,
    CRASH_TIME_DELTA,
    CONFIRMATION,
)

# Simple logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Run the bot - simplified version."""
    
    # Create the Application with minimal timeout config
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .get_updates_read_timeout(30)
        .get_updates_write_timeout(30)
        .get_updates_connect_timeout(30)
        .build()
    )

    # Add conversation handler
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
    application.add_handler(CommandHandler("odeme", odeme_command))

    logger.info("Starting KazaBot...")
    
    # Simple polling - no complex retry logic needed
    application.run_polling(
        poll_interval=2.0,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
