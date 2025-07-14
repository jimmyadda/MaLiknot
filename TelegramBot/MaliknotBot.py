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

from language_utils import get_user_language
from TelegramBot.messages import get_message



logging.basicConfig(level=logging.INFO)
load_dotenv()



BOT_TOKEN = os.getenv("BOT_TOKEN")
FLASK_API_URL = os.getenv("FLASK_API_URL")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_language(update.effective_chat.id)
    msg = get_message("start", lang)
    await update.message.reply_text(msg, parse_mode="Markdown")

    # await update.message.reply_text(
    #     "📋 שלחו רשימת קניות:\n"
    #     " שורה ראשונה – שם הרשימה (למשל: קניות לשבת :)\n"
    #     "✏️ הקפד/י שהשם יסתיים בנקודתיים `:` או מקף `-`\n"
    #     "כדי שנדע שזהו שם הרשימה.\n\n"
    #     " שורה שנייה – פריטים מופרדים בפסיקים\n\n"
    #     " דוגמה:\n"
    #     "-קניות לסופש\n"
    #     "חלב 2, לחם פרוס, עגבנייה 6"
    # )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    lines = update.message.text.strip().splitlines()

    # אם יש לפחות שתי שורות והשורה הראשונה מסתיימת בתו מפריד – זו שם הרשימה
    if len(lines) >= 2 and re.match(r".*[:|\-–—]$", lines[0]):
        name_part = re.sub(r"[:|\-–—]$", "", lines[0]).strip()  # remove the final colon or dash
        list_name = f"[{chat_id}] {name_part}"
        items_text = "\n".join(lines[1:]).strip()
    else:
        list_name = f"[{chat_id}] Telegram List"
        items_text = update.message.text.strip()

    payload = {
        'list_name': list_name,
        'items': items_text,
        'chat_id': chat_id
    }
    response = requests.post(f"{FLASK_API_URL}/add_list_from_telegram", json=payload)
    data = response.json()

    list_id = data['list_id']
    created = data.get('created', False)
    url = f"https://maliknot.up.railway.app/list/{list_id}"

    keyboard = [[
        InlineKeyboardButton(get_message("keyboard.view", lang), callback_data=f"showlist:{list_id}"),
        InlineKeyboardButton(get_message("keyboard.delete", lang), callback_data=f"deletelist:{list_id}"),
        InlineKeyboardButton(get_message("keyboard.duplicate", lang), callback_data=f"duplicatelist:{list_id}")
    ], [
        InlineKeyboardButton(get_message("keyboard.history", lang), url=f"https://maliknot.up.railway.app/user_lists/{chat_id}")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if created:
        lang = get_user_language(chat_id)
        msg = get_message("list_created", lang, list_id=list_id, url=url)
        await update.message.reply_text(msg, reply_markup=reply_markup)
    else:
        lang = get_user_language(chat_id)
        msg = get_message("items_added", lang, list_id=list_id, url=url)
        await update.message.reply_text(msg, reply_markup=reply_markup)

async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data 
    chat_id = query.message.chat_id   
    if data.startswith("showlist:"):
        list_id = int(data.split(":")[1])
        response = requests.get(f"{FLASK_API_URL}/get_list/{list_id}")
        items = response.json().get("items", [])

        if not items:
            await context.bot.send_message(chat_id=query.message.chat_id, text=get_message("list_empty", lang))
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
        await context.bot.send_message(chat_id=query.message.chat_id, text=get_message("list_deleted", lang, list_id=list_id))

    elif data.startswith("duplicatelist:"):
        original_id = int(data.split(":")[1])
        chat_id=query.message.chat_id
        lang = get_user_language(chat_id)
        response = requests.post(f"{FLASK_API_URL}/duplicate_list/{original_id}")
        data = response.json()
        new_id = data['new_id']
        msg = get_message("list_duplicated", lang, list_id=new_id, url=url)

        url = f"https://maliknot.up.railway.app/list/{new_id}"
        keyboard = [[
            InlineKeyboardButton(get_message("keyboard.view", lang), callback_data=f"showlist:{list_id}"),
            InlineKeyboardButton(get_message("keyboard.delete", lang), callback_data=f"deletelist:{list_id}"),
            InlineKeyboardButton(get_message("keyboard.duplicate", lang), callback_data=f"duplicatelist:{list_id}")
        ], [
            InlineKeyboardButton(get_message("keyboard.history", lang), url=f"https://maliknot.up.railway.app/user_lists/{chat_id}")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=msg,
            reply_markup=reply_markup
        )
    
async def error(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f'⚠️ Error: {context.error}')

if __name__ == "__main__":
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    #this line for the expense handler (filter number)
    #application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^\d+(\.\d+)?$'), handle_expense_sum))
    application.add_handler(CallbackQueryHandler(handle_button_press))
    application.add_error_handler(error)

    print("🤖 Telegram bot polling started")
    application.run_polling()
