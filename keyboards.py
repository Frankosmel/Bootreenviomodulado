from telegram import ReplyKeyboardMarkup

MAIN_KB = ReplyKeyboardMarkup([
    ["🔗 Vincular Canal", "➕ Agregar Mensaje"],
    ["📂 Destinos",        "✏️ Editar Mensaje"],
    ["🗑️ Eliminar Mensaje", "🔁 Cambiar Intervalo"],
    ["🌐 Cambiar Zona",     "📄 Estado del Bot"]
], resize_keyboard=True)

BACK_KB = ReplyKeyboardMarkup([["🔙 Volver"]], resize_keyboard=True)
