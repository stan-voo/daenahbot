# config.py - Configuration management
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot configuration - Changed from TELEGRAM_TOKEN to TELEGRAM_BOT_TOKEN
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

# Database configuration
# Use Railway volume for persistent storage
DATABASE_PATH = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH', '')
if DATABASE_PATH:
    DATABASE_PATH = os.path.join(DATABASE_PATH, 'kazabot_db.json')
else:
    # Fallback for local development
    DATABASE_PATH = 'kazabot_db.json'

# Validation constraints
MAX_DESCRIPTION_LENGTH = 200
MIN_CRASH_TIME = 0  # minutes
MAX_CRASH_TIME = 60  # minutes
MAX_REPORTS_PER_DAY = 3
PAYOUT_THRESHOLD = 500  # TL

# Conversation states
LOCATION, PHOTO, DESCRIPTION, CRASH_TIME_DELTA, CONFIRMATION = range(5)

# --- Load Admin User IDs from .env file ---
admin_ids_str = os.getenv('ADMIN_IDS', '') # Get the comma-separated string

# Process the string into a list of integers
if admin_ids_str:
    try:
        # Split the string by commas and convert each part to an integer
        ADMIN_IDS = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',')]
    except ValueError:
        print("Error: ADMIN_IDS in .env file contains non-numeric values. Please check it.")
        ADMIN_IDS = [] # Default to an empty list on error
else:
    # If the variable is not set, default to an empty list
    ADMIN_IDS = []

# It's good practice to log or print the loaded admins on startup to verify
if not ADMIN_IDS:
    print("Warning: No ADMIN_IDS found in .env file. Admin features will be disabled.")
else:
    print(f"Admin users loaded successfully: {ADMIN_IDS}")
