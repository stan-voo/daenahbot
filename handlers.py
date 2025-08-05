# handlers.py
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from database import ( 
    save_report, 
    get_or_create_user, 
    update_user_profile,
    get_user_report_count_today,
    get_report_by_id, 
    update_report_status,
    update_user_balance,
    get_user_by_id
)
from config import ADMIN_IDS, PAYOUT_THRESHOLD, REWARD_AMOUNT, SERVICE_ZONES_TEXT
from localization import STRINGS # <-- Import the localized strings

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define states for the conversation
(
    LOCATION,
    PHOTO,
    DESCRIPTION,
    CRASH_TIME_DELTA,
    CONFIRMATION,
    COMPANY_NAME,
) = range(6)

# Reusable keyboard with localized buttons
NEW_REPORT_KEYBOARD = ReplyKeyboardMarkup(
    [
        [STRINGS['new_report_button']],
        [STRINGS['balance_button'], STRINGS['rules_button'], STRINGS['support_button']]
    ],
    resize_keyboard=True
)

# --- Start & Cancel ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation with a localized welcome message."""
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    
    photo_file_id = 'AgACAgQAAxkBAAPCaIu8_FQu7pFVNR7X8AAB5O_shWW2AALfxzEbZKFhUOKlznwiwuHuAQADAgADeAADNgQ' 
    get_or_create_user(user.id, user.username)

    location_keyboard = KeyboardButton(text=STRINGS['share_location_button'], request_location=True)
    custom_keyboard = [[location_keyboard]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True, one_time_keyboard=True)

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=photo_file_id,
        caption=STRINGS['welcome_caption'],
        reply_markup=reply_markup,
        read_timeout=20,
        write_timeout=20
    )
    return LOCATION

# --- Reporting Flow ---

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the location and asks for a photo using localized text."""
    user_location = update.message.location
    context.user_data['report'] = {
        'location': (user_location.latitude, user_location.longitude),
        'location_timestamp': datetime.utcnow().isoformat()
    }
    logger.info("Location from %s: %s", update.message.from_user.first_name, user_location)
    
    await update.message.reply_text(
        STRINGS['location_received'],
        reply_markup=ReplyKeyboardRemove(),
    )
    return PHOTO

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the photo and asks for a description using localized text."""
    user_photo = update.message.photo[-1]
    context.user_data['report']['photo'] = user_photo.file_id
    context.user_data['report']['photo_timestamp'] = datetime.utcnow().isoformat()
    
    logger.info("Photo received from %s", update.message.from_user.first_name)
    
    reply_keyboard = [[STRINGS['skip_button']]]
    await update.message.reply_text(
        STRINGS['photo_received'],
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True),
    )
    return DESCRIPTION

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the description and asks for the time delta using localized text."""
    user_description = update.message.text
    if user_description.lower() != STRINGS['skip_button'].lower():
        if len(user_description) > 200:
            await update.message.reply_text(STRINGS['description_too_long'])
            return DESCRIPTION
        context.user_data['report']['description'] = user_description
    else:
        context.user_data['report']['description'] = None
        
    logger.info("Description from %s: %s", update.message.from_user.first_name, user_description)
    await update.message.reply_text(
        STRINGS['ask_crash_time'],
        reply_markup=ReplyKeyboardRemove(),
    )
    return CRASH_TIME_DELTA

async def description_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the description and asks for the time delta using localized text."""
    context.user_data['report']['description'] = None
    logger.info("User %s skipped the description.", update.message.from_user.first_name)
    await update.message.reply_text(
        STRINGS['ask_crash_time'],
        reply_markup=ReplyKeyboardRemove(),
    )
    return CRASH_TIME_DELTA

async def crash_time_delta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the time delta and shows a localized summary."""
    text = update.message.text
    try:
        delta = int(text)
        if not (0 <= delta <= 60):
            raise ValueError
        context.user_data['report']['crash_time_delta'] = delta
    except (ValueError, TypeError):
        await update.message.reply_text(STRINGS['invalid_crash_time'])
        return CRASH_TIME_DELTA

    report = context.user_data['report']
    summary = (
        f"{STRINGS['report_summary_header']}\n"
        f"{STRINGS['summary_location']}\n"
        f"{STRINGS['summary_photo']}\n"
        f"{STRINGS['summary_description']}: {report.get('description', 'N/A')}\n"
        f"{STRINGS['summary_crash_time']}: ~{report.get('crash_time_delta')} dakika önce\n\n"
        f"{STRINGS['summary_confirm_prompt']}"
    )
    reply_keyboard = [[STRINGS['submit_report_button'], STRINGS['cancel_button']]]
    await update.message.reply_text(
        summary,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True),
    )
    return CONFIRMATION

async def submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Submits the report and ends the conversation with localized messages."""
    user = update.message.from_user
    report_data = context.user_data.get('report')
    
    if not report_data:
        await update.message.reply_text(STRINGS['generic_error'])
        return ConversationHandler.END

    report_id = save_report(user.id, report_data)
    logger.info("User %s submitted report %s", user.first_name, report_id)

    user_profile = get_or_create_user(user.id, user.username)
    new_count = user_profile.get('report_count', 0) + 1
    update_user_profile(user.id, {'report_count': new_count})
    
    await notify_admins(context, user, report_id, report_data)
    
    await update.message.reply_text(STRINGS['report_submitted'])
    return await finish(update, context)

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Clears user data and shows the final localized message."""
    context.user_data.clear()
    await update.message.reply_text(
        STRINGS['final_message'],
        reply_markup=NEW_REPORT_KEYBOARD,
    )
    return ConversationHandler.END

async def notify_admins(context: ContextTypes.DEFAULT_TYPE, user, report_id, report_data):
    """Sends a localized notification to admins."""
    lat, lon = report_data['location']
    maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"

    admin_message = (
        f"{STRINGS['admin_notification_header']}\n\n"
        f"📍 Konum (Google Haritalar):\n{maps_link}\n\n"
        f"{STRINGS['admin_report_id_label']}: {report_id}\n"
        f"{STRINGS['admin_submitted_by_label']}: @{user.username} (ID: {user.id})\n"
        f"{STRINGS['admin_description_label']}: {report_data.get('description', 'N/A')}\n"
        f"{STRINGS['admin_time_delta_label']}: ~{report_data.get('crash_time_delta')} dakika önce"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Onayla", callback_data=f"approve_{report_id}"),
            InlineKeyboardButton("❌ Reddet", callback_data=f"reject_{report_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(chat_id=admin_id, photo=report_data['photo'])
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            logger.info(f"Sent notification for report {report_id} to admin {admin_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to admin {admin_id}: {e}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the conversation with a localized message."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    context.user_data.clear()
    await update.message.reply_text(
        STRINGS['report_canceled'],
        reply_markup=NEW_REPORT_KEYBOARD,
    )
    return ConversationHandler.END

async def review_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles admin decisions with localized feedback."""
    query = update.callback_query
    await query.answer()

    admin_user = query.from_user
    action, report_id = query.data.split("_")

    report = get_report_by_id(report_id)
    new_status = "onaylandı" if action == "approve" else "reddedildi"
    update_report_status(report_id, new_status, admin_user.id)
    
    final_text = (
        f"{query.message.text}\n\n{STRINGS['admin_decision_header']}\n"
        f"{STRINGS['admin_status_label']} {new_status.upper()} "
        f"{STRINGS['admin_reviewed_by_label']} @{admin_user.username}."
    )
    await query.edit_message_text(text=final_text)

    original_user_id = report['telegram_user_id']
    user_notification = STRINGS['user_update_notification'].format(report_id=report['report_id'], status=new_status)
    
    if action == 'approve':
        reward_amount = 100
        new_balance = update_user_balance(original_user_id, reward_amount)
        user_notification += STRINGS['user_reward_notification'].format(reward_amount=reward_amount, new_balance=new_balance)
    
    try:
        await context.bot.send_message(
            chat_id=original_user_id,
            text=user_notification,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send status update to user {original_user_id}: {e}")

async def odeme_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin-only payout command with localized responses."""
    admin_user_id = update.message.from_user.id
    if admin_user_id not in ADMIN_IDS:
        await update.message.reply_text(STRINGS['payout_unauthorized'])
        return

    try:
        args = context.args
        if len(args) != 2:
            raise ValueError()
        target_user_id, amount = int(args[0]), int(args[1])

        if amount <= 0:
            await update.message.reply_text(STRINGS['payout_must_be_positive'])
            return

        user = get_user_by_id(target_user_id)
        if not user:
            await update.message.reply_text(STRINGS['payout_user_not_found'].format(user_id=target_user_id))
            return

        current_balance = user.get('balance', 0)
        if current_balance < amount:
            await update.message.reply_text(STRINGS['payout_insufficient_balance'].format(user_id=target_user_id, current_balance=current_balance, amount=amount))
            return

        new_balance = update_user_balance(target_user_id, -amount)
        await update.message.reply_text(STRINGS['payout_success_admin'].format(user_id=target_user_id, amount=amount, new_balance=new_balance))
        
        try:
            await context.bot.send_message(chat_id=target_user_id, text=STRINGS['payout_success_user'].format(amount=amount, new_balance=new_balance))
        except Exception as e:
            logger.error(f"Failed to send payout notification to user {target_user_id}: {e}")
            await update.message.reply_text(STRINGS['payout_notification_failed'].format(user_id=target_user_id))

    except (IndexError, ValueError):
        await update.message.reply_text(STRINGS['payout_usage'])

async def bakiye_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the user their balance using localized text."""
    user = get_or_create_user(update.message.from_user.id, update.message.from_user.username)
    balance = user.get('balance', 0)
    await update.message.reply_text(
        STRINGS['balance_info'].format(balance=balance, payout_threshold=PAYOUT_THRESHOLD),
        reply_markup=NEW_REPORT_KEYBOARD
    )

async def kurallar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends the localized list of rules."""
    rules_text = STRINGS['rules_text'].format(
        reward_amount=REWARD_AMOUNT,
        payout_threshold=PAYOUT_THRESHOLD,
        service_zones=SERVICE_ZONES_TEXT
    )
    await update.message.reply_text(
        text=rules_text,
        reply_markup=NEW_REPORT_KEYBOARD,
        parse_mode='Markdown'
    )

async def destek_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provides the localized support message."""
    await update.message.reply_text(
        text=STRINGS['support_text'],
        reply_markup=NEW_REPORT_KEYBOARD,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
