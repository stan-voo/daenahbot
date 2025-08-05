# **Daenah Bot — Next Actions (Updated)**

> **What's new in this update**
>
> * ✅ Implemented payout logic with `/odeme` command
> * ✅ Added essential user commands (`/bakiye`, `/kurallar`, `/destek`)
> * ✅ Enhanced admin notifications with Google Maps links
> * 🎯 Focus shifted to Turkish localization and enhanced user experience
> * 🎯 Planning for secure payout information collection

---

## ✅ **Completed Features (Foundation Complete)**

### **1) Stable Database Using Railway Volumes**
* **Status:** ✅ Completed
* **Implementation:** Persistent volume mounted at `/data`; DB path set to `/data/kazabot_db.json`

### **2) User Balance & Reward System**
* **Status:** ✅ Completed
* **Features:** Starting balance (99 TL), reward per report (100 TL), real-time updates

### **3) Payout Logic**
* **Status:** ✅ Completed
* **Implementation:** Admin-only `/odeme <user_id> <amount>` command with balance validation

### **4) Essential User Commands**
* **Status:** ✅ Completed
* **Commands:** `/bakiye` (balance), `/kurallar` (rules), `/destek` (support)
* **UI:** Persistent keyboard buttons for easy access

### **5) Enhanced Admin Notifications**
* **Status:** ✅ Completed
* **Feature:** Google Maps link in admin notifications for easy location verification

---

## 🎯 **Current Priority: Localization & UX Enhancement**

### **A) Turkish Localization**

**Why:** Your target users are Turkish motor couriers. Full Turkish localization is essential for adoption.

**Action Plan:**
1. **Create a `localization.py` file** with all user-facing strings:
   ```python
   # localization.py
   STRINGS = {
       'welcome_new_user': (
           "Kazabot'a hoş geldiniz! Size katıldığınız için 99 ₺ başlangıç bakiyesi ekledik. "
           "Ekibimiz tarafından doğrulanan her kaza raporu için 100 ₺ ödül kazanacaksınız. "
           "Toplam bakiyeniz 500 ₺'ye ulaştığında kazançlarınızı çekebilirsiniz.\n\n"
           "Hadi başlayalım! Lütfen aşağıdaki butona basarak kazanın konumunu paylaşın."
       ),
       'welcome_returning_user': (
           "Tekrar hoş geldiniz! Yeni bir kaza raporu oluşturmak için aşağıdaki butona basarak "
           "kazanın konumunu paylaşın."
       ),
       'share_location_button': "Kaza Konumunu Paylaş",
       'location_received': "Harika! Şimdi, kazanın net bir fotoğrafını çekip bana gönderin.",
       # ... add all strings
   }
   ```

2. **Update all handlers** to use the localization strings
3. **Translate button labels** in `NEW_REPORT_KEYBOARD`

### **B) Smart Welcome Message Handling**

**Why:** Returning users shouldn't see the full welcome message when clicking "➕ Yeni Rapor"

**Implementation:**
```python
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    user_profile = get_or_create_user(user.id, user.username)
    
    # Check if this is a new user or returning user
    is_new_user = user_profile.get('report_count', 0) == 0
    
    # Send appropriate message
    if is_new_user:
        # Send welcome photo and full message
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=WELCOME_PHOTO_FILE_ID,
            caption=STRINGS['welcome_new_user'],
            reply_markup=location_request_keyboard
        )
    else:
        # Skip photo, send brief message
        await update.message.reply_text(
            STRINGS['welcome_returning_user'],
            reply_markup=location_request_keyboard
        )
    
    return LOCATION
```

### **C) Rejection Reason Feature**

**Why:** Users need to understand why their reports were rejected to improve future submissions

**Database Update:**
```python
# In update_report_status function
def update_report_status(report_id, new_status, admin_id, rejection_reason=None):
    Report = Query()
    update_data = {'status': new_status, 'reviewed_by': admin_id}
    if rejection_reason:
        update_data['rejection_reason'] = rejection_reason
    reports_table.update(update_data, Report.report_id == report_id)
```

**UI Implementation:**
1. **Add rejection reason buttons** in admin notification:
   ```python
   keyboard = [
       [
           InlineKeyboardButton("✅ Onayla", callback_data=f"approve_{report_id}"),
           InlineKeyboardButton("❌ Reddet", callback_data=f"reject_{report_id}")
       ],
       [
           InlineKeyboardButton("🚫 Bölge Dışı", callback_data=f"reject_zone_{report_id}"),
           InlineKeyboardButton("📸 Belirsiz Fotoğraf", callback_data=f"reject_photo_{report_id}")
       ],
       [
           InlineKeyboardButton("⏰ Geç Bildirim", callback_data=f"reject_late_{report_id}"),
           InlineKeyboardButton("🔄 Mükerrer", callback_data=f"reject_duplicate_{report_id}")
       ]
   ]
   ```

2. **Update review_handler** to process rejection reasons
3. **Include reason in user notification**

---

## 🚀 **Next Priority: Secure Payout Information Collection**

### **D) Automatic Payout Eligibility Detection**

**Implementation Plan:**

1. **Add a check after balance updates:**
   ```python
   # In review_handler, after updating balance
   if new_balance >= PAYOUT_THRESHOLD:
       # Check if we already have payout info
       if not user.get('iban') or not user.get('full_name'):
           await trigger_payout_info_collection(original_user_id, context)
   ```

2. **Create payout information collection flow:**
   ```python
   # New conversation states
   COLLECT_IBAN, COLLECT_NAME, CONFIRM_PAYOUT_INFO = range(7, 10)
   
   async def trigger_payout_info_collection(user_id, context):
       message = (
           "🎉 Tebrikler! Bakiyeniz 500 ₺'ye ulaştı ve ödeme almaya hak kazandınız!\n\n"
           "Ödemenizi işleme alabilmemiz için bazı bilgilere ihtiyacımız var.\n"
           "Lütfen IBAN numaranızı gönderin (TR ile başlamalı):"
       )
       await context.bot.send_message(chat_id=user_id, text=message)
   ```

3. **IBAN validation:**
   ```python
   def validate_iban(iban):
       # Remove spaces and convert to uppercase
       iban = iban.replace(' ', '').upper()
       # Check if it starts with TR and has correct length
       if not iban.startswith('TR') or len(iban) != 26:
           return False
       # Additional validation logic here
       return True
   ```

### **E) Secure Sensitive Data Storage**

**Critical Security Measures:**

1. **Create separate secure database for sensitive data:**
   ```python
   # config.py
   SECURE_DB_PATH = os.path.join(DATABASE_PATH, '..', '.secure_kazabot_db.json')
   
   # database.py
   secure_db = TinyDB(SECURE_DB_PATH, indent=4)
   payout_info_table = secure_db.table('payout_info')
   ```

2. **Update `.gitignore`:**
   ```
   .env
   venv/
   __pycache__/
   *.pyc
   db.json
   .DS_Store
   .secure_kazabot_db.json  # Add this
   *secure*.json            # Add this
   ```

3. **Store sensitive data separately:**
   ```python
   def save_payout_info(user_id, iban, full_name):
       PayoutInfo = Query()
       payout_data = {
           'telegram_user_id': user_id,
           'iban': iban,
           'full_name': full_name,
           'created_at': datetime.utcnow().isoformat(),
           'last_updated': datetime.utcnow().isoformat()
       }
       payout_info_table.upsert(payout_data, PayoutInfo.telegram_user_id == user_id)
   ```

4. **Admin command to view payout info:**
   ```python
   async def odeme_bilgileri_command(update, context):
       # Admin-only command to view user payout info
       if update.message.from_user.id not in ADMIN_IDS:
           return
       
       # Parse user_id from command
       # Fetch and display payout info securely
   ```

---

## 📅 **Implementation Roadmap**

### **Week 1 — Localization & UX**
1. Create `localization.py` with all Turkish translations
2. Implement smart welcome message (new vs returning users)
3. Update all user-facing text to Turkish
4. Test with Turkish-speaking users

### **Week 2 — Enhanced Rejection & Payout Flow**
1. Implement rejection reason buttons and database fields
2. Create payout information collection conversation flow
3. Add IBAN validation
4. Set up secure database for sensitive data
5. Test payout eligibility triggers

### **Week 3 — Security & Polish**
1. Implement secure data access patterns
2. Add admin commands for payout info viewing
3. Create data export functionality for admins
4. Comprehensive testing of all flows

---

## 🔒 **Security Best Practices**

1. **Never log sensitive data** - No IBANs or full names in logs
2. **Separate databases** - Keep financial data in separate, gitignored file
3. **Access control** - Only admins can view payout information
4. **Data minimization** - Only collect what's absolutely necessary
5. **Regular backups** - Implement automated secure backups for Railway

---

## 🎯 **Future Enhancements**

* **Automated IBAN validation** via Turkish bank API
* **Payout batch processing** for admins
* **Export to CSV** for accounting purposes
* **Two-factor confirmation** for large payouts
* **Automated zone checking** using geocoding APIs
* **Multi-language support** (Turkish/English toggle)