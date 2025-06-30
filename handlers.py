#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from decorators import admin_only, log_exceptions
from keyboards import MAIN_KB, BACK_KB
from config_manager import load_config, save_config
from mensajes_manager import load_mensajes, save_mensajes
from filters_custom import filter_forwarded_from_origin
from pagination import paginate_list
from datetime import datetime

@admin_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start → muestra el menú principal con estado.
    """
    cfg = load_config()
    mens = load_mensajes()
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

@admin_only
@log_exceptions
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    MessageHandler global: gestiona flujos basados en context.user_data['waiting_for'].
    """
    cfg = load_config()
    mensajes = load_mensajes()
    text = update.message.text or ""
    waiting = context.user_data.get("waiting_for")

    # 1) Vincular Canal
    if text == "🔗 Vincular Canal" and not waiting:
        await update.message.reply_text(
            "📤 Reenvía un mensaje desde tu canal de origen.",
            reply_markup=BACK_KB
        )
        context.user_data["waiting_for"] = "channel_forward"
        return

    if waiting == "channel_forward":
        fchat = getattr(update.message, "forward_from_chat", None)
        if fchat:
            cfg["origen_chat_id"] = str(fchat.id)
            save_config(cfg)
            await update.message.reply_text(
                f"✅ Canal vinculado: `{fchat.id}`",
                parse_mode="Markdown",
                reply_markup=MAIN_KB
            )
            context.user_data.pop("waiting_for")
        return

    # 2) Gestión de Destinos (muestra menú y setea estado)
    if text == "📂 Destinos" and not waiting:
        kb = ReplyKeyboardMarkup([
            ["➕ Agregar Destino", "🗑️ Eliminar Destino"],
            ["📁 Crear Lista", "📂 Gestionar Listas"],
            ["🔙 Volver"]
        ], resize_keyboard=True)
        await update.message.reply_text("📂 Gestión de Destinos", reply_markup=kb)
        context.user_data["waiting_for"] = "destinos_menu"
        return

    # (Aquí añade los flujos: add_destino, del_destino, new_list, manage_lists...)

    # 3) Captura de mensaje reenviado desde origen
    if filter_forwarded_from_origin.filter(update.message):
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
        save_mensajes(mensajes)
        kb = ReplyKeyboardMarkup([
            ["👥 A Todos", "📋 Lista"],
            ["✅ Guardar", "❌ Cancelar"],
            ["🏁 Finalizar"],
            ["🔙 Volver"]
        ], resize_keyboard=True)
        await update.message.reply_text(
            f"🔥 *Nuevo Mensaje Detectado!*\nID: `{mid}`\n"
            f"Intervalo: `{nuevo['intervalo_segundos']}s`\nElige destino:",
            parse_mode="Markdown",
            reply_markup=kb
        )
        context.user_data["waiting_for"] = f"msg_cfg_{len(mensajes)-1}"
        return

    # (Completa aquí los subflujos: msg_cfg, editar/eliminar mensaje, cambiar intervalo, cambiar zona, estado...)

def get_handlers():
    return [
        CommandHandler("start", start),
        MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler)
    ]
