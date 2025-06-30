from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

MAIN_KB = ReplyKeyboardMarkup([
    ["🔗 Vincular Canal", "📂 Destinos"],
    ["✏️ Editar Mensaje", "🗑️ Eliminar Mensaje"],
    ["🔁 Cambiar Intervalo", "🌐 Cambiar Zona"],
    ["📄 Estado del Bot"]
], resize_keyboard=True)

BACK_KB = ReplyKeyboardMarkup([["🔙 Volver"]], resize_keyboard=True)

# Ejemplo de InlineKeyboard:
# CONFIRM_KB = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Sí", callback_data="yes"), InlineKeyboardButton("❌ No", callback_data="no")]])
