import logging
import aiohttp
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder,CommandHandler, MessageHandler, filters, ContextTypes



BOT_TOKEN = '7807618025:AAGKA3jxR2qFsA1F5yfkbaJuqJo40GW5kFs'
FLASK_API_URL = 'https://maliknot.onrender.com/api/add_list_from_telegram'

logging.basicConfig(level=logging.INFO)


#commands
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
                await update.message.reply_text(f"רשימה חדשה נוצרה עם מזהה: {data['list_id']}")
            else:
                await update.message.reply_text("אירעה שגיאה. נסה שוב.")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("שלום, אנא שילחו רשימת קניות מופרדת בפסיקים")

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'update {update} caused error {context.error}')


async def run():
    print("runnaing bot onRender")
    Botapp = ApplicationBuilder().token(BOT_TOKEN).build()
    #commands
    Botapp.add_handler(CommandHandler('start',start_command))
    #messages
    Botapp.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    #errors
    Botapp.add_error_handler(error)
    Botapp.run_polling()


def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run())
    

""" if __name__== '__main__':
    print("runnaing bot locally")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    #commands
    app.add_handler(CommandHandler('start',start_command))
    #messages
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    #errors
    app.add_error_handler(error)
    print("pooling")
    app.run_polling()  """   