from functools import wraps
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config_manager import load_config

# Decorador para restringir el acceso solo al administrador

def admin_only(func):
    """
    Solo permite la ejecución de comandos si el user_id coincide con admin_id de config.
    Si no es admin, responde con mensaje de acceso denegado.
    """
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        cfg = load_config()
        if update.effective_user.id != cfg.get("admin_id"):
            # Opcional: usar teclado principal para volver al menú
            await update.message.reply_text(
                "❌ *Acceso denegado.*", parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup([["/start"]], resize_keyboard=True)
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# Decorador para registrar y manejar excepciones en handlers

def log_exceptions(func):
    """
    Captura excepciones no manejadas en handlers y las registra.
    Informa al usuario sobre un error interno.
    """
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            import logging
            logging.error(f"Error en handler {func.__name__}: {e}", exc_info=True)
            # Informa al usuario
            if update.message:
                await update.message.reply_text("❌ Ha ocurrido un error interno. Por favor intenta nuevamente.")
            elif update.callback_query:
                await update.callback_query.answer("❌ Error interno.")
    return wrapped
