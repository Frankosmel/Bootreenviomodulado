from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from config_manager import load_config

def admin_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        cfg = load_config()
        if update.effective_user.id != cfg.get("admin_id"):
            return await update.message.reply_text("❌ Acceso denegado.")
        return await func(update, context, *args, **kwargs)
    return wrapped
