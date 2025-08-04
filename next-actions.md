# **Daenah Bot Development Plan**
#### **1. Implement Payout Logic**
*   **Verdict:** **Essential.** The core loop of your bot is "Report -> Get Verified -> Get Paid." Without a way to manage payouts, the balance becomes meaningless.
*   **Criticism/Suggestion:** Instead of just "withdrawing" money, think of it as "recording a payout." The admin performs a payout outside the bot (e.g., a bank transfer) and then uses a command to update the bot's database.
*   **MVP Action:** Create a simple admin-only command: `/odeme <user_id> <amount>`.
    *   This command should first check if the person using it is an admin.
    *   It subtracts the `<amount>` from the user's balance in `database.py`.
    *   It sends a confirmation message to the admin (`"Payout of 150 ₺ for user 12345 has been recorded. New balance: 350 ₺"`).
    *   It sends a notification to the user (`"A payout of 150 ₺ has been processed! Your new balance is 350 ₺."`).

#### **2. Add Stable Database Using Railway.app Volumes**
*   **Verdict:** **CRITICAL.** This is non-negotiable. Without this, your bot will lose all user data on every restart or deploy, making it completely unusable.
*   **Criticism/Suggestion:** Your plan is perfect. Using Railway volumes with TinyDB is the ideal intersection of simplicity and persistence for an MVP.
*   **MVP Action:** Follow these exact steps:
    1.  In your Railway project, go to your service settings and add a **Volume**.
    2.  Set the **Mount Path** to `/data`.
    3.  In your `config.py` file, change the database path to use this volume:
        `DATABASE_PATH = '/data/kazabot_db.json'`
    4.  Deploy your bot. Railway will now ensure that the `kazabot_db.json` file persists across restarts.

#### **3. Handle User Deletion/Restart**
*   **Verdict:** **Already solved!** This is a great thing to worry about, but your current implementation handles it correctly.
*   **Clarification:** You are currently using `user.id` (`update.message.from_user.id`) as the unique identifier. This `user_id` is a permanent integer assigned by Telegram to each user account. It **does not change** if a user deletes the chat, blocks the bot, or even changes their @username. Your system will always recognize them correctly when they return.
*   **MVP Action:** No action needed. Be confident that using `user.id` is the correct and robust method.

#### **4. Decide if We Need to Ask for Their Phone Number**
*   **Verdict:** **No, not for the MVP.**
*   **Reasoning:** Every extra piece of information you ask for increases the chance a user will quit. For an MVP, you need to be ruthless about removing friction. You don't have a clear use for the phone number yet. Payouts will likely be done via IBAN, not a phone number. Support can be handled via Telegram itself.
*   **MVP Action:** Postpone this. Only add it later if a clear, unavoidable business need arises.

#### **5. Implement Contact Support Button**
*   **Verdict:** **Essential.** Users will always have questions or issues. A dead end with no support option is frustrating and leads to users abandoning the bot.
*   **MVP Action:** Create a simple `/destek` command in `handlers.py`.
    *   When a user types `/destek`, the bot should reply with a simple message.
    *   **Option A (Easiest):** `"Herhangi bir sorun veya sorun için destek ekibimize destek@yourcompany.com adresinden e-posta gönderebilirsiniz."` (For any questions or issues, you can email our support team at...).
    *   **Option B (Better):** `"Destek talebinizi bu gruba iletebilirsiniz: [Link to a private Telegram group where admins are members]"` (You can forward your support request to this group: ...).

#### **6. Completely Remove the Code for the Company Name Field**
*   **Verdict:** **Excellent idea.** This is good code hygiene.
*   **Reasoning:** Commented-out "dead code" adds clutter and can confuse future development.
*   **MVP Action:**
    1.  Delete the `company_name` function from `handlers.py`.
    2.  Delete the `COMPANY_NAME` state variable from the top of `handlers.py` and from the `ConversationHandler` in `bot.py`.
    3.  In `database.py`, remove `'courier_company': None,` from the `user_profile` dictionary in the `get_or_create_user` function.

#### **7. Add Instructions for Serviceable Zones**
*   **Verdict:** **Essential.** This manages user expectations perfectly and will save you and your users a lot of frustration from rejected reports.
*   **MVP Action:** Add the zone information in two key places:
    1.  **Bot Description (BotFather):** Edit the `/setdescription` text to include a line like: `"(!) Şu anda sadece **İzmir'in Konak ve Bornova** ilçelerindeki raporları kabul ediyoruz."` ((!) We currently only accept reports from the Konak and Bornova districts of Izmir.).
    2.  **Welcome Message (`/start`):** Add the same sentence to the welcome message in `handlers.py` to reinforce it.

#### **8. Implement Automatic Zone Check**
*   **Verdict:** **Postpone.** This is a "nice-to-have" automation, not an MVP essential.
*   **Reasoning:** For an MVP, the admin can and should do this manually. It takes 5 seconds to look at the location on a map. You should only automate this *after* you've proven that:
    a) The bot is getting enough reports to make manual checking a burden.
    b) Out-of-zone reports are a common problem.
*   **MVP Action:** Do nothing. Let the admins manually check the location and reject reports that are out of bounds.

#### **9. Implement Spam Prevention**
*   **Verdict:** **High Priority.** This is a simple and effective protection.
*   **Reasoning:** You've already done the hard work of writing the code!
*   **MVP Action:** In `handlers.py`, find the `start` function and **uncomment** the code block that checks the daily report limit.

    ```python
    # In handlers.py -> start()
    # UNCOMMENT THIS BLOCK
    report_count = get_user_report_count_today(user.id)
    if report_count >= MAX_REPORTS_PER_DAY:
        await update.message.reply_text(
            f"Günlük rapor limitinize ({MAX_REPORTS_PER_DAY}) ulaştınız. Lütfen yarın tekrar deneyin."
        )
        return ConversationHandler.END
    ```

---

### **Further MVP Suggestions**

Here are a few more simple, high-impact features to consider for your MVP:

*   **Add a `/bakiye` (Balance) Command:** Users will want to check their balance without starting a new report. This is a very simple handler that gets the user's profile and replies with their current balance.
*   **Add a `/kurallar` (Rules) Command:** A simple command that reminds the user of the key rules: reward amount, payout threshold (500 ₺), and serviceable zones.
*   **Improve Admin Notifications:** In `notify_admins` in `handlers.py`, you can easily add a Google Maps link to the location. This makes the admin's job much easier.

    ```python
    # In handlers.py -> notify_admins()
    lat, lon = report_data['location']
    maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    admin_message = (
        f"🚨 New Accident Report Submitted 🚨\n\n"
        f"📍 Location: [Open on Google Maps]({maps_link})\n" # Add this link
        # ... rest of the message
    )
    ```

### **Prioritized MVP Roadmap**

Based on this analysis, here is your action plan, sorted by priority:

**Tier 1: Do Immediately (Foundation)**
1.  **Stable Database:** Configure Railway Volumes.
2.  **Remove Company Code:** Clean up the codebase.
3.  **Add Serviceable Zones:** Update BotFather and the `/start` message.
4.  **Implement Spam Prevention:** Uncomment the existing code.

**Tier 2: Do Next (Core Functionality)**
5.  **Implement Payout Logic:** Create the `/odeme` admin command.
6.  **Implement Support:** Create the `/destek` command.
7.  **Add Balance Check:** Create the `/bakiye` command.

**Tier 3: Postpone for Later**
8.  ~~Ask for Phone Number~~ (Decided against for now).
9.  **Automatic Zone Check:** Wait until this becomes a proven pain point.