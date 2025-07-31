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
from database import save_report, get_or_create_user, update_user_profile, get_user_report_count_today
from config import ADMIN_IDS 
from database import ( 
    save_report, 
    get_or_create_user, 
    update_user_profile,
    get_report_by_id, 
    update_report_status,
    update_user_balance # <-- ADD THIS
)

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
# --- NEW: Reusable keyboard for starting a new report ---
NEW_REPORT_KEYBOARD = ReplyKeyboardMarkup([["➕ New Report"]], resize_keyboard=True, one_time_keyboard=False)

# --- Start & Cancel ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation, shows a welcome message, and asks for the accident location."""
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    
    # --- NEW: Send welcome message and image ---
    # Replace 'YOUR_FILE_ID_HERE' with the actual file_id you obtained
    photo_file_id = 'AgACAgQAAxkBAAPCaIu8_FQu7pFVNR7X8AAB5O_shWW2AALfxzEbZKFhUOKlznwiwuHuAQADAgADeAADNgQ' 
    welcome_caption = (
        "Welcome to Kazabot! We've added a starting balance of 99 ₺ to your account for joining us. "
        "For every accident report you submit that is verified by our team, you will earn a 100 ₺ reward. "
        "You can withdraw your earnings once your total balance reaches 500 ₺.\n\n"
        "Let's get started! Please share the accident's location by pressing the button below."
    )
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=photo_file_id,
        caption=welcome_caption,
        read_timeout=20,
        write_timeout=20
    )
    # --- End of new section ---
    
    # Onboard the user if they are new and set initial balance
    get_or_create_user(user.id, user.username)

    location_keyboard = KeyboardButton(text="Share Accident Location", request_location=True)
    custom_keyboard = [[location_keyboard]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "Please press the button below to share the accident's location.",
        reply_markup=reply_markup,
    )
    return LOCATION

# --- Reporting Flow ---

async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the location and asks for a photo."""
    user_location = update.message.location
    context.user_data['report'] = {
        'location': (user_location.latitude, user_location.longitude),
        'location_timestamp': datetime.utcnow().isoformat()
    }
    logger.info("Location from %s: %s", update.message.from_user.first_name, user_location)
    
    await update.message.reply_text(
        "Great! Now, please take a clear photo of the accident and send it to me.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return PHOTO

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the photo and asks for a description."""
    user_photo = update.message.photo[-1] # Get the highest resolution photo
    context.user_data['report']['photo'] = user_photo.file_id
    context.user_data['report']['photo_timestamp'] = datetime.utcnow().isoformat()
    
    logger.info("Photo received from %s", update.message.from_user.first_name)
    
    reply_keyboard = [["Skip"]]
    await update.message.reply_text(
        "Photo received. Now, please add a short description (e.g., 'two cars, rear-end'). "
        "This is optional. You can also type 'Skip'.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True),
    )
    return DESCRIPTION

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the description and asks for the time delta."""
    user_description = update.message.text
    if user_description.lower() != 'skip':
        if len(user_description) > 200:
            await update.message.reply_text("The description is too long (max 200 characters). Please try again.")
            return DESCRIPTION
        context.user_data['report']['description'] = user_description
    else:
        context.user_data['report']['description'] = None
        
    logger.info("Description from %s: %s", update.message.from_user.first_name, user_description)
    await update.message.reply_text(
        "Got it. Roughly how many minutes ago did the crash happen? (Please enter a number from 0 to 60)",
        reply_markup=ReplyKeyboardRemove(),
    )
    return CRASH_TIME_DELTA

async def description_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the description and asks for the time delta."""
    context.user_data['report']['description'] = None
    logger.info("User %s skipped the description.", update.message.from_user.first_name)
    await update.message.reply_text(
        "Description skipped. Roughly how many minutes ago did the crash happen? (Please enter a number from 0 to 60)",
        reply_markup=ReplyKeyboardRemove(),
    )
    return CRASH_TIME_DELTA


async def crash_time_delta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the time delta and asks for final confirmation."""
    text = update.message.text
    try:
        delta = int(text)
        if not (0 <= delta <= 60):
            raise ValueError
        context.user_data['report']['crash_time_delta'] = delta
    except (ValueError, TypeError):
        await update.message.reply_text("That's not a valid number. Please enter a number between 0 and 60.")
        return CRASH_TIME_DELTA

    # Show summary
    report = context.user_data['report']
    summary = (
        f"--- REVIEW YOUR REPORT ---\n"
        f"📍 Location: Sent\n"
        f"📸 Photo: Sent\n"
        f"📝 Description: {report.get('description', 'N/A')}\n"
        f"⏱️ Time Since Crash: ~{report.get('crash_time_delta')} minutes ago\n\n"
        "Is everything correct?"
    )
    reply_keyboard = [["Submit Report", "Cancel"]]
    await update.message.reply_text(
        summary,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True),
    )
    return CONFIRMATION

async def submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Submits the report, saves it, and transitions to the final steps."""
    user = update.message.from_user
    report_data = context.user_data.get('report')
    
    if not report_data:
        await update.message.reply_text("Something went wrong. Please start over with /start.")
        return ConversationHandler.END

    # Save the report
    report_id = save_report(user.id, report_data)
    logger.info("User %s submitted report %s", user.first_name, report_id)

    # Update user's report count
    user_profile = get_or_create_user(user.id, user.username)
    new_count = user_profile.get('report_count', 0) + 1
    update_user_profile(user.id, {'report_count': new_count})
    
    # Notify admins
    await notify_admins(context, user, report_id, report_data)
    
    # --- MODIFICATION: Temporarily disable company name question ---
    # if user_profile.get('courier_company') is None:
    #     await update.message.reply_text(
    #         "✅ Success! Your report has been submitted.\n\n"
    #         "To help us, could you tell us which courier company you work for? (e.g., 'Getir', 'Trendyol Go'). This is optional.",
    #          reply_markup=ReplyKeyboardRemove(),
    #     )
    #     return COMPANY_NAME
    # else:
    #     # If company name is known, end the conversation
    #     return await finish(update, context)
    await update.message.reply_text("✅ Success! Your report has been submitted.\n\n")
    return await finish(update, context) # Always go to the finish state
    # --- End of modification ---


# --- MODIFICATION: Comment out the unused handler ---
# async def company_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Saves the user's courier company and ends the conversation."""
#     user_id = update.message.from_user.id
#     company = update.message.text
    
#     update_user_profile(user_id, {'courier_company': company})
#     logger.info("User %s set their company to %s", update.message.from_user.first_name, company)
    
#     await update.message.reply_text("Thank you! Your profile has been updated.")
    
#     return await finish(update, context)
# --- End of modification ---


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Clears user data and shows the final message with the 'New Report' button."""
    context.user_data.clear()
    await update.message.reply_text(
        "You can now submit a new report or close this chat.",
        reply_markup=NEW_REPORT_KEYBOARD,
    )
    return ConversationHandler.END


async def notify_admins(context: ContextTypes.DEFAULT_TYPE, user, report_id, report_data):
    """Sends a notification to all admins about a new report."""
    admin_message = (
        f"🚨 New Accident Report Submitted 🚨\n\n"
        f"Report ID: {report_id}\n"
        f"Submitted By: @{user.username} (ID: {user.id})\n"
        f"Description: {report_data.get('description', 'N/A')}\n"
        f"Time Delta: ~{report_data.get('crash_time_delta')} minutes ago"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{report_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{report_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(chat_id=admin_id, photo=report_data['photo'])
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                reply_markup=reply_markup
            )
            logger.info(f"Sent notification for report {report_id} to admin {admin_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to admin {admin_id}: {e}")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the conversation and shows the 'New Report' button."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    context.user_data.clear()
    await update.message.reply_text(
        "Report canceled. You can start a new one anytime.",
        reply_markup=NEW_REPORT_KEYBOARD, # Use our new keyboard
    )
    return ConversationHandler.END


async def review_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles admin decisions from inline keyboard buttons."""
    query = update.callback_query
    await query.answer() # Acknowledge the button press

    admin_user = query.from_user
    action, report_id = query.data.split("_")

    if admin_user.id not in ADMIN_IDS:
        await query.edit_message_text(text="Sorry, you are not authorized to perform this action.")
        return

    report = get_report_by_id(report_id)
    if not report:
        await query.edit_message_text(text=f"Error: Report {report_id} not found.")
        return
    
    if report['status'] != 'pending':
        await query.edit_message_text(text=f"This report has already been reviewed. Status: {report['status']}.")
        return

    # Update status and notify the user
    new_status = "verified" if action == "approve" else "rejected"
    update_report_status(report_id, new_status, admin_user.id)
    
    # Update the admin's message to show the result
    final_text = query.message.text + f"\n\n--- Decision ---\nStatus set to {new_status.upper()} by @{admin_user.username}."
    await query.edit_message_text(text=final_text)

    # Notify the original user
    original_user_id = report['telegram_user_id']
    user_notification = f"UPDATE: Your report (ID: {report['report_id']}) has been {new_status}."
    
    if new_status == 'verified':
        # --- NEW: Update balance and notify user ---
        reward_amount = 100 # Define your reward amount here
        new_balance = update_user_balance(original_user_id, reward_amount)
        user_notification += (
            f"\n\nCongratulations! {reward_amount} TL has been added to your account. "
            f"Your new balance is {new_balance} TL."
        )
        # --- End of new section ---
    
    try:
        await context.bot.send_message(
            chat_id=original_user_id,
            text=user_notification
        )
    except Exception as e:
        logger.error(f"Failed to send status update to user {original_user_id}: {e}")
