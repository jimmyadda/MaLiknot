import asyncio
import logging
import re
import time
from dotenv import load_dotenv
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
import os

from language_utils import get_user_language, save_user_language
from bot_messages import get_message
from ocr_utils import extract_text_from_image_bytes



logging.basicConfig(level=logging.INFO)
load_dotenv()


""" with open("sample.jpg", "rb") as f:
    print(extract_text_from_image_bytes(f.read())) """

BOT_TOKEN = os.getenv("BOT_TOKEN")
FLASK_API_URL = os.getenv("FLASK_API_URL")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Get current language or fallback
    lang = get_user_language(chat_id) or update.effective_user.language_code or "en"
    lang = lang[:2]

    # Get localized message
    message_text = get_message("start", lang)

    # Add language selection buttons
    keyboard = [
        [
            InlineKeyboardButton("🇮🇱 עברית", callback_data="lang:he"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
            InlineKeyboardButton("🇫🇷 Français", callback_data="lang:fr")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = get_user_language(chat_id)
    now = time.time()
    ready_at = context.user_data.get("ocr_ready_at", 0)

    # ✅ Block too-fast replies only if OCR just happened
    if now < ready_at:
        await update.message.reply_text(get_message("ocr_too_fast", lang))
        return

    text = update.message.text
    lines = text.strip().splitlines()

    if len(lines) >= 2 and re.match(r".*[:|\-–—]$", lines[0]):
        name_part = re.sub(r"[:|\-–—]$", "", lines[0]).strip()
        list_name = f"[{chat_id}] {name_part}"
        items_text = "\n".join(lines[1:]).strip()
    else:
        list_name = f"[{chat_id}] Telegram List"
        items_text = text.strip()

    items_text = normalize_text(items_text)

    payload = {
        "list_name": list_name,
        "items": items_text,
        "chat_id": chat_id
    }

    import requests
    response = requests.post(f"{FLASK_API_URL}/add_list_from_telegram", json=payload)
    data = response.json()

    list_id = data["list_id"]
    created = data.get("created", False)
    url = f"https://maliknot.up.railway.app/list/{list_id}?from_telegram=true"

    keyboard = [[
        InlineKeyboardButton(get_message("keyboard.view", lang), callback_data=f"showlist:{list_id}"),
        InlineKeyboardButton(get_message("keyboard.delete", lang), callback_data=f"deletelist:{list_id}"),
        InlineKeyboardButton(get_message("keyboard.duplicate", lang), callback_data=f"duplicatelist:{list_id}")
    ], [
        InlineKeyboardButton(get_message("keyboard.history", lang), url=f"https://maliknot.up.railway.app/user_lists/{chat_id}?from_telegram=true")
    ]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    msg = (
        get_message("list_created", lang, list_id=list_id, url=url)
        if created else
        get_message("items_added", lang, list_id=list_id, url=url)
    )

    await update.message.reply_text(msg, reply_markup=reply_markup)

async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data 
    chat_id = query.message.chat_id 
    lang = get_user_language(chat_id)
      
    if data.startswith("showlist:"):
        list_id = int(data.split(":")[1])
        response = requests.get(f"{FLASK_API_URL}/get_list/{list_id}")
        items = response.json().get("items", [])

        if not items:
            await context.bot.send_message(chat_id=query.message.chat_id, text=get_message("list_empty", lang))
            return
        message_title = get_message("list_header", lang, list_id=list_id)
        message = message_title
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
        print("list_id",list_id)
        print("chat_id",chat_id)
        ok = requests.delete(f"{FLASK_API_URL}/delete_list/{list_id}")
        if ok:
            await context.bot.send_message(chat_id=chat_id, text=get_message("list_deleted", lang, list_id=list_id))

    elif data.startswith("duplicatelist:"):
        original_id = int(data.split(":")[1])
        chat_id=query.message.chat_id
        lang = get_user_language(chat_id)
        response = requests.post(f"{FLASK_API_URL}/duplicate_list/{original_id}")
        data = response.json()
        new_id = data['new_id']

        url = f"https://maliknot.up.railway.app/list/{new_id}?from_telegram=true"
        msg = get_message("list_duplicated", lang, list_id=new_id, url=url)
        
        keyboard = [[
            InlineKeyboardButton(get_message("keyboard.view", lang), callback_data=f"showlist:{new_id}"),
            InlineKeyboardButton(get_message("keyboard.delete", lang), callback_data=f"deletelist:{new_id}"),
            InlineKeyboardButton(get_message("keyboard.duplicate", lang), callback_data=f"duplicatelist:{new_id}")
        ], [
            InlineKeyboardButton(get_message("keyboard.history", lang), url=f"https://maliknot.up.railway.app/user_lists/{chat_id}?from_telegram=true")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=msg,
            reply_markup=reply_markup
        )
    
    elif data.startswith("lang:"):
        lang = data.split(":")[1]
        chat_id = query.message.chat_id
        save_user_language(chat_id, lang)

        await context.bot.send_message(
            chat_id=chat_id,
            text=get_message("language_set", lang)
        )
        #Send  /start message in new language
        await context.bot.send_message(
            chat_id=chat_id,
            text=get_message("start", lang),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🇮🇱 עברית", callback_data="lang:he"),
                    InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
                    InlineKeyboardButton("🇫🇷 Français", callback_data="lang:fr")
                ]
            ])
        )
        return    

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()

    chat_id = update.effective_chat.id
    lang = get_user_language(chat_id)

    await update.message.reply_text(get_message("ocr_processing", lang))

    try:
        result = extract_text_from_image_bytes(bytes(image_bytes))

        if not result.strip():
            await update.message.reply_text(get_message("ocr_no_text", lang))
            return

        context.user_data["last_ocr_text"] = result

        await update.message.reply_text(get_message("ocr_copy_instruction", lang))
        await update.message.reply_text(result, parse_mode=None)

        # ✅ Allow user to respond after 2 seconds
        context.user_data["ocr_ready_at"] = time.time() + 2
    except Exception as e:
        await update.message.reply_text(get_message("ocr_error", lang, error=str(e)))
           
async def error(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f'⚠️ Error: {context.error}')

def normalize_text(text: str) -> str:
    import unicodedata
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("،", ",").replace("，", ",").replace("﹐", ",")
    text = re.sub(r"[\u200c\u200d\u202c\u202d\uFEFF\u00A0]", "", text)
    text = re.sub(r"\s*,\s*", ",", text)
    return text.strip()


if __name__ == "__main__":
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    #this line for the expense handler (filter number)
    #application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^\d+(\.\d+)?$'), handle_expense_sum))
    application.add_handler(CallbackQueryHandler(handle_button_press))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_error_handler(error)

    print("🤖 Telegram bot polling started")
    application.run_polling()
