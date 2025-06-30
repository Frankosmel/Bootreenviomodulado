from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from decorators import admin_only
from keyboards import MAIN_KB, BACK_KB

@admin_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bienvenido al Bot de Reenvío", reply_markup=MAIN_KB)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Lógica de flujos según context.user_data['waiting_for']
    pass


def get_handlers():
    return [
        CommandHandler('start', start),
        MessageHandler(filters.ALL, message_handler)
    ]
