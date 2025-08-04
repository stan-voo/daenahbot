# database.py
import uuid
import logging
from datetime import datetime, timedelta
from tinydb import TinyDB, Query
from config import DATABASE_PATH

# Enable logging
logger = logging.getLogger(__name__)

# Initialize the database with the path from config
db = TinyDB(DATABASE_PATH, indent=4)
reports_table = db.table('reports')
users_table = db.table('users')

def save_report(user_id, report_data):
    """
    Saves a new accident report to the database.
    """
    report_id = str(uuid.uuid4())
    submitted_at = datetime.utcnow().isoformat()

    report = {
        'report_id': report_id,
        'telegram_user_id': user_id,
        'location_geo': report_data.get('location'),
        'location_time': report_data.get('location_timestamp'),
        'photo_file_id': report_data.get('photo'),
        'photo_time': report_data.get('photo_timestamp'),
        'description': report_data.get('description'),
        'crash_time_delta': report_data.get('crash_time_delta'),
        'submitted_at': submitted_at,
        'status': 'pending', # pending/verified/duplicate/rewarded
        'reward_sent': False
    }
    reports_table.insert(report)
    return report_id

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

def update_user_profile(user_id, data_to_update):
    """
    Updates a user's profile with new information (e.g., company, report count).
    """
    User = Query()
    users_table.update(data_to_update, User.telegram_user_id == user_id)

def get_user_report_count_today(user_id):
    """
    Counts how many reports a user has submitted in the last 24 hours.
    """
    Report = Query()
    twenty_four_hours_ago = (datetime.utcnow() - timedelta(days=1)).isoformat()
    
    user_reports = reports_table.search(
        (Report.telegram_user_id == user_id) & 
        (Report.submitted_at >= twenty_four_hours_ago)
    )
    return len(user_reports)
    # database.py (add these functions)

def get_report_by_id(report_id):
    """Retrieves a single report by its unique ID."""
    Report = Query()
    report = reports_table.get(Report.report_id == report_id)
    return report

def update_report_status(report_id, new_status, admin_id):
    """Updates the status of a report and logs which admin did it."""
    Report = Query()
    reports_table.update(
        {'status': new_status, 'reviewed_by': admin_id}, 
        Report.report_id == report_id
    )
