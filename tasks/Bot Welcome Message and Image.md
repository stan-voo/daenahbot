Bot Welcome Message and Image.md
Of course. Here is the extracted text, translation, and a comprehensive plan to implement the requested features, along with recommendations for your database strategy.

### **1. Bot Welcome Message and Image**

Here is the extracted text from the image and its English translation.

**Original Turkish Text:**

> **Kazayı Bildir, Kazan!**
> Bu bot üzerinden gördüğünüz trafik kazalarını bize bildirebilir ve kazanç sağlayabilirsiniz.
> 
> 🚗 Kaza yerinden bir fotoğraf çekip, konum bilgisiyle birlikte gönderin.
> ✅ Bilgiler doğrulandıktan sonra, 24 saat içinde hesabınıza 1000 TL yatırılır.
> 📞 Bilgiler doğruysa, destek ekibimiz sizinle iletişime geçecektir.
> 
> Unutmayın, hem hayat kurtarın hem de kazanç sağlayın!

**English Translation:**

> **Report an Accident, Get Rewarded!**
> You can report traffic accidents you see through this bot and earn rewards.
> 
> 🚗 Take a photo at the scene of the accident and send it along with the location information.
> ✅ After the information is verified, 1000 TL will be deposited into your account within 24 hours.
> 📞 If the information is correct, our support team will contact you.
> 
> Don't forget, you can both save lives and earn rewards!

---

### **2. Implementation Plan**

Here is a step-by-step plan to implement all the requested changes in your codebase.

#### **Part A: Add the Welcome Image and Message**

1.  **Get the Image File ID:** To send the image without re-uploading it every time, you need its `file_id`.
    *   Send the image to your bot yourself.
    *   In the bot's console logs, you will see the incoming message data. Find the `file_id` for the photo you sent. It will be a long string of characters.
    *   Copy this `file_id`.

2.  **Update the `start` function in `handlers.py`:** Modify the `start` function to send the photo and the new welcome text.

    ```python
    # handlers.py

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Starts the conversation, shows a welcome message, and asks for the accident location."""
        user = update.message.from_user
        logger.info("User %s started the conversation.", user.first_name)
        
        # --- NEW: Send welcome message and image ---
        # Replace 'YOUR_FILE_ID_HERE' with the actual file_id you obtained
        photo_file_id = 'YOUR_FILE_ID_HERE' 
        welcome_caption = (
            "Welcome to KazaBot!\n\n"
            "Report an Accident, Get Rewarded!\n"
            "You can report traffic accidents you see through this bot and earn rewards.\n\n"
            "🚗 Take a photo at the scene of the accident and send it along with the location information.\n"
            "✅ After the information is verified, you will receive a reward.\n"
            "📞 If the information is correct, our support team will contact you.\n\n"
            "Don't forget, you can both save lives and earn rewards!"
        )
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=photo_file_id,
            caption=welcome_caption
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
    ```

#### **Part B: Implement User Balance**

1.  **Update `database.py`:** Modify the user creation function to include the balance and add a function to update it.

    ```python
    # database.py

    def get_or_create_user(user_id, username):
        """
        Retrieves a user profile or creates a new one with an initial balance.
        """
        User = Query()
        user = users_table.get(User.telegram_user_id == user_id)

        if not user:
            user_profile = {
                'telegram_user_id': user_id,
                'username': username,
                'created_at': datetime.utcnow().isoformat(),
                'courier_company': None,
                'payment_method': None,
                'report_count': 0,
                'balance': 99  # NEW: Add initial balance of 99 Lira
            }
            users_table.insert(user_profile)
            return user_profile
        return user

    def update_user_balance(user_id, amount_to_add):
        """
        Increments a user's balance by a specified amount.
        """
        User = Query()
        user = users_table.get(User.telegram_user_id == user_id)
        if user:
            # Handle cases where older users might not have a balance field
            current_balance = user.get('balance', 0) 
            new_balance = current_balance + amount_to_add
            users_table.update({'balance': new_balance}, User.telegram_user_id == user_id)
            logger.info(f"Updated balance for user {user_id}. New balance: {new_balance}")
            return new_balance
        return None
    ```    *Note: You will also need to import `logger` in `database.py` if it's not already there: `import logging` and `logger = logging.getLogger(__name__)`.*

2.  **Update `handlers.py`:** Modify the `review_handler` to award Lira for approved reports.

    ```python
    # handlers.py

    # IMPORTANT: Add the new database function to the imports
    from database import ( 
        save_report, 
        get_or_create_user, 
        update_user_profile,
        get_report_by_id, 
        update_report_status,
        update_user_balance # <-- ADD THIS
    )

    async def review_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # ... (keep the existing code until the user notification part)

        # Update status and notify the user
        new_status = "verified" if action == "approve" else "rejected"
        update_report_status(report_id, new_status, admin_user.id)
        
        # Update the admin's message to show the result
        final_text = query.message.text + f"\n\n--- Decision ---\nStatus set to *{new_status.upper()}* by @{admin_user.username}."
        await query.edit_message_text(text=final_text, parse_mode='Markdown')

        # Notify the original user
        original_user_id = report['telegram_user_id']
        user_notification = f"UPDATE: Your report (ID: {report_id}) has been *{new_status}*."
        
        if new_status == 'verified':
            # --- NEW: Update balance and notify user ---
            reward_amount = 150 # Define your reward amount here
            new_balance = update_user_balance(original_user_id, reward_amount)
            user_notification += (
                f"\n\nCongratulations! {reward_amount} Lira has been added to your account. "
                f"Your new balance is {new_balance} Lira."
            )
            # --- End of new section ---
        
        try:
            await context.bot.send_message(
                chat_id=original_user_id,
                text=user_notification,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send status update to user {original_user_id}: {e}")
    ```

#### **Part C: Temporarily Disable "Company Name" Question**

1.  **Update `handlers.py`:** Comment out the logic that asks for the company name.

    ```python
    # handlers.py

    async def submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Submits the report, saves it, and ends the conversation."""
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
    ```

2.  **Update `bot.py`:** Comment out the unused state in the `ConversationHandler`.

    ```python
    # bot.py

    # ... (other imports)
    from handlers import (
        # ... (other handlers)
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

    # ...

    def main() -> None:
        # ...

        conv_handler = ConversationHandler(
            # ...
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
            per_message=False 
        )
        # ...
    ```

---

### **3. Database Storage on Railway.app for an MVP**

For an MVP hosted on Railway, you have two excellent choices for handling your `kazabot_db.json` file. Here’s a comparison to help you decide:

#### **Option 1: Railway Persistent Volume (Recommended for MVP)**

Railway allows you to mount a persistent disk, called a "volume," to your service. This volume acts like a small, attached hard drive that doesn't get erased when you deploy new code or restart your service.

*   **How it Works:** You would configure a volume in your Railway project settings and mount it at a specific path (e.g., `/data`). You would then modify your `DATABASE_PATH` in `config.py` to point to this location (e.g., `DATABASE_PATH = '/data/kazabot_db.json'`).
*   **Pros:**
    *   **Simplicity:** It's the easiest and quickest setup. You stay entirely within the Railway ecosystem.
    *   **Low Latency:** The database file is stored on the same infrastructure as your bot, ensuring fast access.
    *   **Cost-Effective:** Using a small volume is generally included in Railway's free/hobby tier or is very inexpensive.
*   **Cons:**
    *   **Manual Backups:** You are responsible for backing up the JSON file yourself.
    *   **Scalability Limitations:** If your bot becomes extremely popular with high write volumes, a simple JSON file can become a bottleneck.

#### **Option 2: External Database Service (e.g., Supabase)**

Supabase is a "backend-as-a-service" platform that provides a full-featured PostgreSQL database, authentication, and more.

*   **How it Works:** You would create a project on Supabase, get your database connection credentials, and add them to your bot's environment variables on Railway. Your bot would then connect to Supabase over the internet. This would require replacing `TinyDB` with a PostgreSQL client library like `psycopg2-binary`.
*   **Pros:**
    *   **Highly Scalable:** A real SQL database can handle much more data and concurrent users.
    *   **Managed Service:** Supabase handles backups, security, and maintenance for you.
    *   **Powerful Features:** You get a data browser, user management, and API endpoints out of the box.
*   **Cons:**
    *   **Increased Complexity:** You would need to rewrite your entire `database.py` file to work with PostgreSQL instead of TinyDB. This is a significant code change.
    *   **Potential for Higher Latency:** The database connection happens over the network, which can be slightly slower than a local file.
    *   **Learning Curve:** Requires understanding SQL and managing a new service.

**Recommendation for Your MVP:**

**Stick with Railway's persistent volume and TinyDB.**

For an MVP, the primary goal is to test your idea quickly and with minimal complexity. The combination of TinyDB and a Railway volume is perfectly suited for this. It is robust enough to handle the initial user load, and the setup is incredibly straightforward. You can focus on building bot features rather than managing database infrastructure.

If your bot proves successful and you need to scale, migrating to a service like Supabase is a great next step, but it is unnecessary at this early stage.