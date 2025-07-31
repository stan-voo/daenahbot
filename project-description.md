### **DaenahBot: A Real-Time Car Accident Reporting Telegram Bot**

This document outlines the technical implementation of DaenahBot, a Telegram bot designed for motor couriers in Turkey to report minor car accidents in real-time. This MVP focuses on rapid data collection and user engagement.

### 1. Core Technologies

*   **Programming Language:** Python
*   **Telegram Bot Framework:** The project uses `python-telegram-bot`, a comprehensive library for building Telegram bots.
*   **Database:** `TinyDB` is employed as a lightweight, file-based database, suitable for the project's current scale.

### 2. Project Structure

The project is organized into several Python files, ensuring a modular and maintainable codebase:

*   `bot.py`: The main application entry point that initializes the bot and its handlers.
*   `handlers.py`: Defines all the conversation and command handlers, managing the user interaction flow.
*   `database.py`: Manages all interactions with the `TinyDB` database, including saving and retrieving user and report data.
*   `config.py`: Stores configuration variables, such as the Telegram bot token and admin user IDs, loaded from an environment file.
*   `requirements.txt`: Lists all Python dependencies for the project.
*   `Procfile`: Specifies the command to be executed by the web server to run the application.
*   `kazabot_db.json`: The TinyDB JSON file that serves as the database.
*   `.gitignore`: Specifies intentionally untracked files to be ignored by Git.

### 3. Detailed Implementation

#### **Step 1: Environment and Configuration**

The project uses a `.env` file to manage environment variables, most notably the `TELEGRAM_BOT_TOKEN`. The `config.py` file loads these variables and defines application-wide constants such as database path, validation constraints, and conversation states. It also loads a list of admin user IDs for administrative features.

#### **Step 2: Database and Data Management**

The `database.py` script initializes a `TinyDB` database stored in `kazabot_db.json`. It provides functions to:

*   Save new accident reports with a unique ID, user information, and timestamps.
*   Create or retrieve user profiles, storing their Telegram ID, username, and report count.
*   Update user profiles, for instance, to add their courier company or increment their report count.
*   Retrieve a specific report by its ID.
*   Update a report's status (e.g., to 'verified' or 'rejected') and record which admin reviewed it.

A notable deviation from the initial plan is the absence of a dedicated `models.py` file with Pydantic models for data validation. Data validation is instead handled within the handler functions.

#### **Step 3: Bot Logic and User Flow**

The core of the bot's functionality is built around a `ConversationHandler` from the `python-telegram-bot` library. This manages the stateful, step-by-step process of submitting an accident report.

The implemented conversation states are:

*   **LOCATION:** Asks for and receives the user's location.
*   **PHOTO:** Prompts for and stores a photo of the accident.
*   **DESCRIPTION:** Asks for an optional text description of the incident.
*   **CRASH_TIME_DELTA:** Inquires about the time elapsed since the accident.
*   **CONFIRMATION:** Displays a summary of the report and asks for user confirmation before submission.
*   **COMPANY_NAME:** After the first report, it asks the user for their courier company to enrich their profile.

**User Onboarding:** The bot creates a user profile upon their first interaction. After a successful report, it prompts for the courier company they work for.

#### **Step 4: Admin Features and Notifications**

A significant feature implemented is the admin notification and review system:

*   **Admin Notification:** Upon a new report submission, a notification is sent to all admin users defined in the `ADMIN_IDS` configuration. This message includes the report details and a photo.
*   **Inline Keyboard for Review:** The admin notification includes an inline keyboard with "Approve" and "Reject" buttons.
*   **Review Handling:** A `CallbackQueryHandler` processes the admin's choice. It updates the report's status in the database and notifies the original user of the outcome.

#### **Step 5: User Interface and Experience**

The bot utilizes `ReplyKeyboardMarkup` for interactive buttons, such as "Share Accident Location" and a persistent "➕ New Report" button, which allows users to easily start a new report after completing or canceling a previous one.

### **Summary of Implemented vs. Planned Features**

| Feature | Initial Plan | Implemented Reality |
| :--- | :--- | :--- |
| **Core Framework** | `python-telegram-bot`, `TinyDB` | Fully implemented as planned. |
| **Data Models** | Pydantic models in `models.py` | Not implemented. Data validation is handled directly in handlers. |
| **User Flow** | `ConversationHandler` with states for location, photo, description, time delta, and confirmation. | Fully implemented, with an additional state for capturing the user's company name. |
| **User Onboarding** | Low-friction onboarding, asking for company name after the first report. | Implemented as planned. |
| **Spam Prevention**| Rate limiting of 3 reports per user per 24 hours. | The code for this is commented out in `handlers.py` and is therefore not active. |
| **Admin Features**| Direct database access for manual verification. | A more advanced system with Telegram notifications and an inline keyboard for report approval/rejection was built. |
| **Reward System** | A `status` field in the database to track report verification and reward status. | The `status` field (`pending`, `verified`, `rejected`) and a `reward_sent` boolean are in the database. A message about potential rewards is sent for verified reports. The actual payout logic is not implemented. |