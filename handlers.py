#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from decorators import admin_only, log_exceptions
from keyboards import MAIN_KB, BACK_KB
from config_manager import load_config, save_config
import mensajes_manager
from filters_custom import filter_forwarded_from_origin
from datetime import datetime

@admin_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = load_config()
    mens = mensajes_manager.load_mensajes()
    text = (
        "🚀 *Menú Principal*\n\n"
        f"📺 Origen: `{cfg.get('origen_chat_id','No asignado')}`\n"
        f"👥 Destinos: {len(cfg.get('destinos',[]))}\n"
        f"📁 Listas: {len(cfg.get('listas_destinos',{}))}\n"
        f"📨 Mensajes: {len(mens)}\n"
        f"⏱️ Intervalo: {cfg.get('intervalo_segundos',60)}s\n"
        f"🌐 Zona: `{cfg.get('timezone','UTC')}`\n\n"
        "Selecciona una opción:"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=MAIN_KB)
    context.user_data.clear()

@admin_only
@log_exceptions
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = load_config()
    mensajes = mensajes_manager.load_mensajes()
    text = update.message.text or ""
    waiting = context.user_data.get("waiting_for")

    # 1) Iniciar vinculación de canal
    if text == "🔗 Vincular Canal" and not waiting:
        await update.message.reply_text(
            "📤 *Reenvía un mensaje* desde tu canal de origen para vincularlo.",
            parse_mode="Markdown",
            reply_markup=BACK_KB
        )
        context.user_data["waiting_for"] = "channel_forward"
        return

    # 1b) Procesar mensaje reenviado para canal
    if waiting == "channel_forward":
        fchat = getattr(update.message, "forward_from_chat", None)
        if fchat:
            cid = str(fchat.id)
            cfg["origen_chat_id"] = cid
            save_config(cfg)
            await update.message.reply_text(
                f"✅ Canal vinculado correctamente: `{cid}`",
                parse_mode="Markdown",
                reply_markup=MAIN_KB
            )
            context.user_data.pop("waiting_for")
        else:
            # No se envió un forward: pedir de nuevo
            await update.message.reply_text(
                "❌ Ese no es un mensaje reenviado. *Intenta de nuevo*.",
                parse_mode="Markdown",
                reply_markup=BACK_KB
            )
        return

    # 2) (El resto de tus flujos…)
    # …
    # Ejemplo de captura:
    if filter_forwarded_from_origin.filter(update.message) and not waiting:
        mid = update.message.forward_from_message_id
        nuevo = {
            "from_chat_id": update.message.forward_from_chat.id,
            "message_id": mid,
            "intervalo_segundos": cfg.get("intervalo_segundos", 60),
            "dest_all": True,
            "dest_list": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        mensajes.append(nuevo)
        mensajes_manager.save_mensajes(mensajes)
        kb = ReplyKeyboardMarkup(
            [["👥 A Todos", "📋 Lista"], ["✅ Guardar", "❌ Cancelar"], ["🏁 Finalizar"], ["🔙 Volver"]],
            resize_keyboard=True
        )
        await update.message.reply_text(
            f"🔥 *Nuevo Mensaje Detectado!*\nID: `{mid}`\nIntervalo: `{nuevo['intervalo_segundos']}s`\nElige destino:",
            parse_mode="Markdown",
            reply_markup=kb
        )
        context.user_data["waiting_for"] = f"msg_cfg_{len(mensajes)-1}"
        return

    # …y así con los demás botones y subflujos

def get_handlers():
    return [
        CommandHandler("start", start),
        MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler)
    ]
