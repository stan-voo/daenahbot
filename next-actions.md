# **Daenah Bot — Next Actions (Updated)**

> **What’s new in this update**
>
> * Added **/kurallar (Rules)** command that was missing.
> * Reinstated the explicit decision: **do not collect phone numbers** in the MVP.
> * Documented that **Telegram ********`user.id`******** is stable** (no action required).
> * Clarified **admin notification link** format to avoid `parse_mode` issues.

---

## ✅ **Completed Foundation (Tier 1)**

### **1) Stable Database Using Railway Volumes**

* **Status:** ✅ Completed
* **Implementation:** Persistent volume mounted at `/data`; DB path set to `/data/kazabot_db.json`.
* **Remote Read (one-liner):**

  ```bash
  railway ssh -- cat /data/kazabot_db.json > local_backup.json
  ```
* **Result:** Data persists across deploys/restarts.

### **2) User Balance & Reward System**

* **Status:** ✅ Completed
* **Notes:**

  * Starting balance for new users (configurable)
  * +100 ₺ (configurable) for each verified report
  * Real‑time balance updates

### **3) Remove Company Name Flow & UX Cleanup**

* **Status:** ✅ Completed
* **Impact:** Fewer fields → higher completion rate

### **4) Error-Resistant Communications**

* **Status:** ✅ Completed
* **Decision:** Avoid `parse_mode` to prevent crashes from user input; prefer plain text/URLs.

---

## 🎯 **Current Priority (Tier 2)**

### **A) Implement Payout Logic**

* **Why:** Core loop is *Report → Verify → Get Paid*.
* **Command:** Admin-only `/odeme <user_id> <amount>`
* **Spec:**

  * Reject if caller is not in `ADMIN_IDS`.
  * Subtract `<amount>` from user balance (insist on sufficient funds).
  * Confirm to admin; notify the user.
* **Sample (python-telegram-bot v20 async):**

  ```python
  async def odeme_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
      if update.message.from_user.id not in ADMIN_IDS:
          await update.message.reply_text("Unauthorized command.")
          return
      try:
          user_id, amount = int(context.args[0]), int(context.args[1])
      except (IndexError, ValueError):
          await update.message.reply_text("Usage: /odeme <user_id> <amount>")
          return

      user = get_user_by_id(user_id)
      if not user:
          await update.message.reply_text("User not found.")
          return

      if user.get('balance', 0) < amount:
          await update.message.reply_text("Insufficient balance for payout.")
          return

      new_balance = update_user_balance(user_id, -amount)
      await update.message.reply_text(
          f"Payout of {amount} ₺ for user {user_id} recorded. New balance: {new_balance} ₺"
      )
      await context.bot.send_message(
          chat_id=user_id,
          text=f"A payout of {amount} ₺ has been processed! Your new balance is {new_balance} ₺."
      )
  ```

### **B) Add Essential User Commands**

#### **1. ********`/bakiye`******** — Balance Check**

```python
async def bakiye_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_or_create_user(user_id, update.message.from_user.username)
    balance = user.get('balance', 0)
    await update.message.reply_text(
        f"💰 Bakiye: {balance} ₺\n\n" \
        f"Ödeme talebi için eşik: {PAYOUT_THRESHOLD} ₺."
    )
```

#### **2. ********`/kurallar`******** — Rules (MISSING → ADDED)**

> Communicate the 3 key constraints clearly and consistently: **reward amount**, **payout threshold**, **serviceable zones**.

```python
RULES_TEXT = (
    "📜 Kurallar\n\n"
    f"• Doğrulanan rapor ödülü: {REWARD_AMOUNT} ₺\n"
    f"• Ödeme talebi eşiği: {PAYOUT_THRESHOLD} ₺\n"
    f"• Hizmet bölgeleri: {SERVICE_ZONES_TEXT}\n\n"
    "Lütfen sadece hizmet bölgeleri içindeki kazaları bildirin.\n"
)

async def kurallar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(RULES_TEXT)
```

* **Config suggestions:**

  ```python
  REWARD_AMOUNT = 100
  PAYOUT_THRESHOLD = 500
  SERVICE_ZONES_TEXT = "İzmir — Konak ve Bornova ilçeleri"
  ```

#### **3. ********`/destek`******** — Support Contact**

```python
async def destek_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 Destek: support@daenah.com\nTelegram: @DaenahSupport\nYanıt süresi: 24 saat içinde"
    )
```

### **C) Service Zone Management**

* **Welcome Message:** Add explicit zone notice (same text as in `/kurallar`).
* **BotFather ********`/setdescription`********:** Include the zone restriction line.
* **Admin Notifications:** Include a **plain URL** to Google Maps to keep `parse_mode` off.

```python
lat, lon = report_data['location']
maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
admin_message = (
    "🚨 New Accident Report Submitted 🚨\n\n"
    f"📍 Location (Google Maps): {maps_link}\n"
    f"Report ID: {report_id}\n"
    f"Submitted By: @{user.username} (ID: {user.id})\n"
    f"Description: {report_data.get('description', 'N/A')}\n"
    f"Time Delta: ~{report_data.get('crash_time_delta')} minutes ago"
)
```

### **D) Enable Spam Prevention**

```python
report_count = get_user_report_count_today(user.id)
if report_count >= MAX_REPORTS_PER_DAY:
    await update.message.reply_text(
        f"Günlük rapor limitinize ({MAX_REPORTS_PER_DAY}) ulaştınız. Lütfen yarın tekrar deneyin."
    )
    return ConversationHandler.END
```

---

## 🧭 **Clarifications That Avoid Wasted Work**

### **1) User Identity Handling — No Action Needed**

* Using `update.message.from_user.id` as the primary key is **correct and stable**. It does **not** change if the user deletes the chat, changes @username, or blocks/unblocks the bot.

### **2) Phone Number Collection — Postponed (MVP)**

* Additional fields create friction and reduce conversion.
* Current needs (payouts via IBAN, support via Telegram/email) do **not** require phone numbers.
* **Revisit** only if a **clear, validated** business need emerges.

---

## 🚀 **Future Enhancements (Tier 3)**

* **Automated QA:** Service zone auto-check; duplicate detection; basic photo quality checks
* **Analytics:** Submission patterns, cohort retention; geographic heatmaps
* **Scaling:** TinyDB → PostgreSQL (>1,000 active users); multi‑language; potential external API integrations

---

## 📅 **Immediate Plan (Next 2 Weeks)**

### **Week 1 — Core Commands**

1. Implement `/odeme` (admin payouts)
2. Add `/bakiye` (balance)
3. **Add ********`/kurallar`******** (rules)** ← *new*
4. Add `/destek` (support)
5. E2E test payout flow

### **Week 2 — UX & Governance**

1. Update welcome message with zone notice
2. Update BotFather description with zone notice
3. Switch admin notification to **plain URL** maps link
4. Enable spam prevention block
