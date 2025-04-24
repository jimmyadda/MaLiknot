import logging
import aiohttp
import asyncio
import threading
from flask import Flask
from telegram import Update,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder,CommandHandler, MessageHandler, filters, ContextTypes,CallbackQueryHandler

from HandelDB import database_read,database_write



BOT_TOKEN = '7807618025:AAGKA3jxR2qFsA1F5yfkbaJuqJo40GW5kFs'
FLASK_API_URL = 'https://maliknot.onrender.com/api/add_list_from_telegram' #PROD
#FLASK_API_URL = 'http://127.0.0.1:5000/api/add_list_from_telegram' #test
logging.basicConfig(level=logging.INFO)


#commands

""" async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the press

    data = query.data

    if data.startswith("showlist:"):
        list_id = int(data.split(":")[1])

        # Fetch items from Flask or DB directly if accessible
        from HandelDB import database_read  # or wherever your DB logic is

        items = database_read(
            SELECT p.name, pl.quantity, pl.notes
            FROM product_in_list pl
            JOIN products p ON p.id = pl.product_id
            WHERE pl.list_id = ?
        , (list_id,))
        print(items)
        if not items:
            await context.bot.send_message(chat_id=query.message.chat_id, text="❌ הרשימה ריקה או לא קיימת.")
            return

        message = f"📋 רשימת קניות #{list_id}:\n"
        for item in items:
            name = item['name']
            quantity = item['quantity']
            note = item['note']
            line = f"- {name} ({quantity})"
            if note:
                line += f" - {note}"
            message += line + "\n"
        
        print(message)
        print(query.message.chat_id)
        await context.bot.send_message(chat_id=query.message.chat_id, text=message)  # ✅ sends a new message
        #await query.edit_message_text(message)
 """

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    print(f'user ({chat_id}) sent: "{text}"')

    payload = {
        'list_name': f"List from {chat_id}",
        'items': text
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(FLASK_API_URL, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                list_id = data['list_id']
                url = f"https://maliknot.onrender.com/telegramlist/{list_id}"

                # Create inline keyboard with a button
                keyboard = [
                            InlineKeyboardButton("📋 הצג את הרשימה", callback_data=f"showlist:{list_id}"),
                            InlineKeyboardButton("🗑 מחק", callback_data=f"deletelist:{list_id}"),
                            InlineKeyboardButton("🔁 שכפל", callback_data=f"duplicatelist:{list_id}")
                ]            
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    f"✅ רשימה חדשה נוצרה עם מזהה: {list_id}",
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text("❌ אירעה שגיאה. נסה שוב.")

#buttons
async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # ✅ Always respond to Telegram or the button will appear stuck
    data = query.data
    
    print(f"Callback data received: {data}")

    if data.startswith("showlist:"):
        list_id = int(data.split(":")[1])

        # Fetch list items from your DB
        items = database_read("""
            SELECT p.name, pl.quantity, pl.notes,pl.collected
            FROM product_in_list pl
            JOIN products p ON p.id = pl.product_id
            WHERE pl.list_id = ?
        """, (list_id,))
         
        if not items:
            await context.bot.send_message(chat_id=query.message.chat_id, text="❌ הרשימה ריקה או לא קיימת.")
            return

        message = f"📋 רשימת קניות #{list_id}:\n"
        for item in items:
            name = item['name']
            quantity = item['quantity']
            note = item['notes']
            collected = item['collected']
            status = "✅" if collected > 0 else "❌"
            line = f"- {name} ({quantity}) collected: {status}"
            if note:
                line += f" - {note}"
            message += line + "\n"
        await context.bot.send_message(chat_id=query.message.chat_id, text=message)

    elif data.startswith("deletelist:"):
        list_id = int(data.split(":")[1])
        database_write("DELETE FROM product_in_list WHERE list_id = ?", (list_id,))
        database_write("DELETE FROM lists WHERE id = ?", (list_id,))
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"🗑 הרשימה {list_id} נמחקה.")

    elif data.startswith("duplicatelist:"):
        original_id = int(data.split(":")[1])
        # Get original list
        original = database_read("SELECT name FROM lists WHERE id = ?", (original_id,))
        if not original:
            await context.bot.send_message(chat_id=query.message.chat_id, text="❌ הרשימה לא נמצאה.")
            return

        new_name = original[0]['name'] + " (העתק)"
        database_write("INSERT INTO lists (name) VALUES (?)", (new_name,))
        new_id = database_read("SELECT max(id) as id FROM lists")[0]['id']

        # Copy items
        items = database_read("SELECT product_id, quantity, notes FROM product_in_list WHERE list_id = ?", (original_id,))
        for item in items:
            database_write(
                "INSERT INTO product_in_list (list_id, product_id, quantity, collected, notes) VALUES (?, ?, ?, 0, ?)",
                (new_id, item['product_id'], item['quantity'], item['notes'])
            )

        await context.bot.send_message(chat_id=query.message.chat_id, text=f"🔁 הרשימה שוכפלה. מזהה חדש: {new_id}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(".שלום, אנא שילחו רשימת קניות מופרדת בפסיקים")
    await update.message.reply_text("פורמט: product [quantity] [note]")
    await update.message.reply_text("לדוגמא: חלב 2, תפוח 5 ירוק, לחם 1 פרוס")
  
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'update {update} caused error {context.error}')


def run_bot():
    print("runnaing bot onRender")
    Botapp = ApplicationBuilder().token(BOT_TOKEN).build()
    #commands
    Botapp.add_handler(CommandHandler('start',start_command))
    #messages
    Botapp.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    Botapp.add_handler(CallbackQueryHandler(handle_button_press))
    #errors
    Botapp.add_error_handler(error)
    print("pooling...")

    Botapp.run_polling()
 