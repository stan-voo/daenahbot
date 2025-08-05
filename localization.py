# localization.py

STRINGS = {
    # --- Button Labels ---
    'share_location_button': "Kaza Konumunu Paylaş",
    'new_report_button': "➕ Yeni Rapor",
    'balance_button': "💰 Bakiye",
    'rules_button': "📜 Kurallar",
    'support_button': "📞 Destek",
    'skip_button': "Atla",
    'submit_report_button': "Raporu Gönder",
    'cancel_button': "İptal",

    # --- Welcome & Onboarding ---
    'welcome_caption': (
        "Kazabot'a hoş geldiniz! Bize katıldığınız için hesabınıza 99 ₺ başlangıç bakiyesi ekledik. "
        "Ekibimiz tarafından doğrulanan her kaza raporu için 100 ₺ ödül kazanacaksınız. "
        "Toplam bakiyeniz 500 ₺'ye ulaştığında kazancınızı çekebilirsiniz.\n\n"
        "Hadi başlayalım! Lütfen aşağıdaki butona basarak kazanın konumunu paylaşın."
    ),

    # --- Reporting Flow ---
    'location_received': "Harika! Şimdi, lütfen kazanın net bir fotoğrafını çekip bana gönderin.",
    'photo_received': "Fotoğraf alındı. Şimdi, lütfen kısa bir açıklama ekleyin (ör. 'iki araba, arkadan çarpma'). Bu isteğe bağlıdır. 'Atla' tuşuna basarak da geçebilirsiniz.",
    'description_too_long': "Açıklama çok uzun (en fazla 200 karakter). Lütfen tekrar deneyin.",
    'ask_crash_time': "Anlaşıldı. Kaza yaklaşık kaç dakika önce oldu? (Lütfen 0 ile 60 arasında bir sayı girin)",
    'invalid_crash_time': "Bu geçerli bir sayı değil. Lütfen 0 ile 60 arasında bir sayı girin.",
    'report_summary_header': "--- RAPORUNUZU GÖZDEN GEÇİRİN ---",
    'summary_location': "📍 Konum: Gönderildi",
    'summary_photo': "📸 Fotoğraf: Gönderildi",
    'summary_description': "📝 Açıklama",
    'summary_crash_time': "⏱️ Kaza Zamanı",
    'summary_confirm_prompt': "Her şey doğru mu?",
    'report_submitted': "✅ Başarılı! Raporunuz gönderildi.\n\n",
    'report_canceled': "Rapor iptal edildi. İstediğiniz zaman yenisini başlatabilirsiniz.",
    'generic_error': "Bir şeyler yanlış gitti. Lütfen /start ile yeniden başlayın.",
    'final_message': "Şimdi yeni bir rapor gönderebilir veya bu sohbeti kapatabilirsiniz.",

    # --- User Commands ---
    'balance_info': "💰 Mevcut Bakiyeniz: {balance} ₺\n\nÖdeme talebinde bulunabilmek için ulaşmanız gereken bakiye: {payout_threshold} ₺.",
    'rules_text': (
        "📜 **KazaBot Kuralları**\n\n"
        "• Doğrulanmış raporlar için ödül: **{reward_amount} ₺**.\n"
        "• Ödeme alt limiti: **{payout_threshold} ₺**.\n"
        "• Hizmet bölgelerimiz: **{service_zones}**.\n\n"
        "Lütfen sadece belirtilen hizmet bölgelerindeki kazaları bildirin. İşbirliğiniz için teşekkür ederiz!"
    ),
    'support_text': (
        "Yardıma mı ihtiyacınız var?\n\n"
        "Tüm sorularınız, sorunlarınız veya geri bildirimleriniz için destek ekibimizle doğrudan iletişime geçebilirsiniz. "
        "Lütfen aşağıdaki linke tıklayın:\n\n"
        "➡️ **[Destek Sohbetini Başlat](https://t.me/mrvooooo)**\n\n"
        "Ekibimiz en kısa sürede size yardımcı olacaktır."
    ),

    # --- Admin & System Messages ---
    'admin_notification_header': "🚨 Yeni Kaza Raporu Gönderildi 🚨",
    'admin_report_id_label': "Rapor ID",
    'admin_submitted_by_label': "Gönderen",
    'admin_description_label': "Açıklama",
    'admin_time_delta_label': "Geçen Süre",
    'admin_decision_header': "--- Karar ---",
    'admin_status_label': "Durum",
    'admin_reviewed_by_label': "tarafından",
    'user_update_notification': "GÜNCELLEME: Raporunuz (ID: {report_id}) *{status}* olarak işaretlendi.",
    'user_reward_notification': "\n\nTebrikler! Hesabınıza {reward_amount} TL eklendi. Yeni bakiyeniz {new_balance} TL.",

    # --- Payout Command (Admin) ---
    'payout_unauthorized': "Bu komut sadece yöneticiler içindir.",
    'payout_usage': "Kullanım: /odeme <user_id> <amount>",
    'payout_must_be_positive': "Ödeme tutarı pozitif bir sayı olmalıdır.",
    'payout_user_not_found': "ID'si {user_id} olan kullanıcı bulunamadı.",
    'payout_insufficient_balance': "Kullanıcı {user_id} için yetersiz bakiye.\nMevcut Bakiye: {current_balance} ₺\nÖdeme Tutarı: {amount} ₺",
    'payout_success_admin': "✅ Kullanıcı {user_id} için {amount} ₺ tutarındaki ödeme kaydedildi.\nYeni bakiyesi şimdi {new_balance} ₺.",
    'payout_success_user': "{amount} ₺ tutarındaki ödeme ekibimiz tarafından işlendi! Yeni bakiyeniz {new_balance} ₺.",
    'payout_notification_failed': "⚠️ Kullanıcı {user_id} tarafına bildirim gönderilemedi.",
}
