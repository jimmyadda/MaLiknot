Ma Liknot - Smart Grocery List App
==================================

This app combines a web interface with a Telegram bot to help you manage grocery lists quickly and easily.

LIVE DEMO
---------
Web App: https://maliknot1bot.pythonanywhere.com
Demo User Login:
- Username: admin
- Password: pass

TELEGRAM BOT
------------
Bot Username: @Maliknot_bot
Link: https://t.me/Maliknot_bot

BOT FEATURES
------------
- Send a message like:
    חלב 2, תפוח 5 ירוק, לחם 1 פרוס

  The bot will:
  - Create a new list
  - Parse products, quantities, and notes
  - Reply with:
    ✅ List ID confirmation
    📋 "View List" button (opens chat message with item breakdown)
    🗑 "Delete" button (removes the list)
    🔁 "Duplicate" button (creates a copy of the list)

- The list is automatically stored in the web app.

- You can also click buttons to view the list with ✅ for collected and ❌ for uncollected items.

WEB APP FEATURES (Flask)
-------------------------
- Web interface to:
  - View all grocery lists
  - Add new items
  - Mark items as collected
  - Automatically detect when all items are collected
  - Optional: trigger a Telegram message when the list is completed

- All changes made in the web app are reflected in Telegram (and vice versa)

TECH STACK
----------
- Python 3 / Flask
- SQLite
- Bootstrap 5 + jQuery
- python-telegram-bot library
- Hosted on pythonanywhere (https://pythonanywhere.com)

TRY IT OUT
----------
1. Visit https://maliknot1bot.pythonanywhere.com
2. Log in using:
   Username: admin
   Password: pass
3. Or send a list to the bot: @Maliknot_bot

Enjoy!
