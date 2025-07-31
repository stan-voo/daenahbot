# bot.py

import logging
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
        # company_name, # Comment out
    cancel,
    review_handler,
    LOCATION,
    PHOTO,
    DESCRIPTION,
    CRASH_TIME_DELTA,
    CONFIRMATION,
        # COMPANY_NAME, # Comment out
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            # NEW: Add an entry point for our button
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
            # COMPANY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_name)], # Comment out this line
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False # Ensures conversation context is consistent
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(review_handler))

    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot...")
    application.run_polling()
    logger.info("Bot stopped.")


if __name__ == "__main__":
    main()