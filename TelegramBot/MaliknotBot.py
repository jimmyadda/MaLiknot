import logging
import re
from dotenv import load_dotenv
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
import os



logging.basicConfig(level=logging.INFO)
load_dotenv()



BOT_TOKEN = os.getenv("BOT_TOKEN")
FLASK_API_URL = os.getenv("FLASK_API_URL")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 שלחו רשימת קניות:\n"
        " שורה ראשונה – שם הרשימה (למשל: קניות לשבת)\n"
        " שורה שנייה – פריטים מופרדים בפסיקים\n\n"
        " דוגמה:\n"
        "קניות לסופ\"ש\n"
        "חלב 2, לחם פרוס, עגבנייה 6"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    lines = update.message.text.strip().splitlines()

    # אם יש לפחות שתי שורות – השורה הראשונה היא שם הרשימה
    if len(lines) >= 2:
        first_line = lines[0].strip()
        if first_line.startswith("[") and first_line.endswith("]"):
            name_part = first_line[1:-1].strip()
        else:
            name_part = first_line
        list_name = f"[{chat_id}] {name_part}"
        items_text = "\n".join(lines[1:]).strip()
    else:
        list_name = f"[{chat_id}] Telegram List"
        items_text = update.message.text.strip()

    payload = {
        'list_name': f"List from {chat_id}",
        'items': text,
        'chat_id': chat_id 
    }
    response = requests.post(f"{FLASK_API_URL}/add_list_from_telegram", json=payload)
    data = response.json()

    list_id = data['list_id']
    created = data.get('created', False)
    url = f"https://maliknot.up.railway.app/list/{list_id}"

    keyboard = [[
        InlineKeyboardButton("📋 הצג את הרשימה", callback_data=f"showlist:{list_id}"),
        InlineKeyboardButton("🗑 מחק", callback_data=f"deletelist:{list_id}"),
        InlineKeyboardButton("🔁 שכפל", callback_data=f"duplicatelist:{list_id}")
    ],
        [
            InlineKeyboardButton("📊 היסטוריית רשימות", url=f"https://maliknot.up.railway.app/user_lists/{chat_id}")
        ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if created:
        await update.message.reply_text(
            f"✅ רשימה חדשה נוצרה! {list_id}\n📋 לצפייה ברשימה: {url}",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"✅ הפריטים התווספו לרשימה {list_id}!\n📋 לצפייה ברשימה: {url}",
            reply_markup=reply_markup
        )

async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data    
    if data.startswith("showlist:"):
        list_id = int(data.split(":")[1])
        response = requests.get(f"{FLASK_API_URL}/get_list/{list_id}")
        items = response.json().get("items", [])

        if not items:
            await context.bot.send_message(chat_id=query.message.chat_id, text="❌ הרשימה ריקה או לא קיימת.")
            return

        message = f"📋 רשימת קניות #{list_id}:\n"
        for item in items:
            name = item['name']
            quantity = item['quantity']
            note = item.get('notes', '')
            collected = item.get('collected', 0)
            status = "✅" if collected else "❌"
            line = f"- {name} ({quantity}) collected: {status}"
            if note:
                line += f" - {note}"
            message += line + "\n"

        await context.bot.send_message(chat_id=query.message.chat_id, text=message)

    elif data.startswith("deletelist:"):
        list_id = int(data.split(":")[1])
        requests.delete(f"{FLASK_API_URL}/delete_list/{list_id}")
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"🗑 הרשימה {list_id} נמחקה.")

    elif data.startswith("duplicatelist:"):
        original_id = int(data.split(":")[1])
        response = requests.post(f"{FLASK_API_URL}/duplicate_list/{original_id}")
        data = response.json()
        new_id = data['new_id']
        url = f"https://maliknot.up.railway.app/list/{new_id}"
        keyboard = [[
            InlineKeyboardButton("📋 הצג את הרשימה", callback_data=f"showlist:{new_id}"),
            InlineKeyboardButton("🗑 מחק", callback_data=f"deletelist:{new_id}"),
            InlineKeyboardButton("🔁 שכפל", callback_data=f"duplicatelist:{new_id}")
        ],
        [
            InlineKeyboardButton("📊 היסטוריית רשימות", url=f"https://maliknot.up.railway.app/user_lists/{original_id}")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"🔁 הרשימה שוכפלה. מזהה חדש: {new_id} \n📋 לצפייה ברשימה: {url} ",
            reply_markup=reply_markup
        )


async def handle_expense_sum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    # Check that it's a valid number
    if not re.fullmatch(r"\d+(\.\d+)?", text):
        return

    payload = {
        "chat_id": str(chat_id),
        "amount": float(text)
    }

    try:
        response = requests.post(f"{FLASK_API_URL}/save_expense", json=payload)
        if response.status_code == 200:
            data = response.json()
            list_id = data.get("list_id")
            await update.message.reply_text(f"✅ הסכום {text} ש״ח נשמר עבור רשימה {list_id}.")
        else:
            await update.message.reply_text("❌ לא נמצאה רשימה שסיימת לאחרונה או שקרתה שגיאה.")
    except Exception as e:
        print(f"Error sending expense to API: {e}")
        await update.message.reply_text("⚠️ שגיאה בשליחה לשרת.")

    
async def error(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f'⚠️ Error: {context.error}')

if __name__ == "__main__":
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    #this line for the expense handler (filter number)
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^\d+(\.\d+)?$'), handle_expense_sum))
    application.add_handler(CallbackQueryHandler(handle_button_press))
    application.add_error_handler(error)

    print("🤖 Telegram bot polling started")
    application.run_polling()
