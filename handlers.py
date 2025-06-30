#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, MessageHandler, filters
)
from decorators import admin_only, log_exceptions
from keyboards import MAIN_KB, BACK_KB
from config_manager import load_config, save_config
import mensajes_manager
from filters_custom import filter_forwarded_from_origin
from pagination import paginate_list
from datetime import datetime
import pytz

# Paginación para edición/eliminación
ITEMS_PER_PAGE = 3

@admin_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start → muestra el menú principal con estado actual."""
    cfg = load_config()
    mens = mensajes_manager.load_mensajes()
    text = (
        "🚀 *Menú Principal*\n\n"
        f"📺 Origen: `{cfg.get('origen_chat_id','No asignado')}`\n"
        f"👥 Destinos: {len(cfg.get('destinos',[]))}\n"
        f"📁 Listas: {len(cfg.get('listas_destinos',{}))}\n"
        f"📨 Mensajes: {len(mens)}\n"
        f"⏱️ Intervalo global: {cfg.get('intervalo_segundos',60)}s\n"
        f"🌐 Zona: `{cfg.get('timezone','UTC')}`\n\n"
        "Selecciona una opción:"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=MAIN_KB)
    context.user_data.clear()

@admin_only
@log_exceptions
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Manejador global: controla los flujos según context.user_data['waiting_for'].
    """
    cfg = load_config()
    mensajes = mensajes_manager.load_mensajes()
    text = update.message.text or ""
    waiting = context.user_data.get("waiting_for")

    # ── AUTO-VINCULACIÓN DE CANAL ──
    fwd_chat = getattr(update.message, "forward_from_chat", None)
    if not cfg.get("origen_chat_id") and fwd_chat:
        cid = str(fwd_chat.id)
        cfg["origen_chat_id"] = cid
        save_config(cfg)
        await update.message.reply_text(
            f"✅ Canal vinculado correctamente: `{cid}`",
            parse_mode="Markdown",
            reply_markup=MAIN_KB
        )
        context.user_data.pop("waiting_for", None)
        return

    # ── 1) Vincular Canal manual ──
    if text == "🔗 Vincular Canal" and not waiting:
        await update.message.reply_text(
            "📤 *Reenvía un mensaje* desde tu canal de origen para vincularlo.",
            parse_mode="Markdown",
            reply_markup=BACK_KB
        )
        context.user_data["waiting_for"] = "channel_forward"
        return

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
            await update.message.reply_text(
                "❌ Ese no es un mensaje reenviado. *Intenta de nuevo*.",
                parse_mode="Markdown",
                reply_markup=BACK_KB
            )
        return

    # ── 2) Gestión de Destinos ──
    if text == "📂 Destinos" and not waiting:
        kb = ReplyKeyboardMarkup([
            ["➕ Agregar Destino", "🗑️ Eliminar Destino"],
            ["📁 Crear Lista", "📂 Gestionar Listas"],
            ["🔙 Volver"]
        ], resize_keyboard=True)
        await update.message.reply_text("📂 *Gestión de Destinos*", parse_mode="Markdown", reply_markup=kb)
        context.user_data["waiting_for"] = "destinos_menu"
        return

    if waiting == "destinos_menu":
        if text == "➕ Agregar Destino":
            await update.message.reply_text("📝 Envía el ID del destino:", reply_markup=BACK_KB)
            context.user_data["waiting_for"] = "add_destino"
        elif text == "🗑️ Eliminar Destino":
            ds = cfg.get("destinos", [])
            if not ds:
                await update.message.reply_text("⚠️ No hay destinos configurados.", reply_markup=MAIN_KB)
                context.user_data.pop("waiting_for")
            else:
                lines = "\n".join(f"{i+1}. {d}" for i, d in enumerate(ds))
                await update.message.reply_text(f"🗑️ Selecciona número para eliminar:\n{lines}", reply_markup=BACK_KB)
                context.user_data["waiting_for"] = "del_destino"
        elif text == "📁 Crear Lista":
            await update.message.reply_text("📌 Nombre de la nueva lista:", reply_markup=BACK_KB)
            context.user_data["waiting_for"] = "new_list_name"
        elif text == "📂 Gestionar Listas":
            lists = cfg.get("listas_destinos", {})
            if not lists:
                await update.message.reply_text("⚠️ No hay listas creadas.", reply_markup=MAIN_KB)
                context.user_data.pop("waiting_for")
            else:
                menu = [[n] for n in lists] + [["🔙 Volver"]]
                await update.message.reply_text("📂 *Listas Disponibles:*", parse_mode="Markdown",
                                                reply_markup=ReplyKeyboardMarkup(menu, resize_keyboard=True))
                context.user_data["waiting_for"] = "manage_lists"
        elif text == "🔙 Volver":
            await start(update, context)
        return

    if waiting == "add_destino":
        d = text.strip()
        lst = cfg.setdefault("destinos", [])
        if d and d not in lst:
            lst.append(d)
            save_config(cfg)
            await update.message.reply_text(f"✅ Destino `{d}` agregado.", reply_markup=MAIN_KB)
        else:
            await update.message.reply_text("⚠️ ID inválido o ya existe.", reply_markup=MAIN_KB)
        context.user_data.pop("waiting_for")
        return

    if waiting == "del_destino":
        try:
            idx = int(text) - 1
            d = cfg["destinos"].pop(idx)
            save_config(cfg)
            await update.message.reply_text(f"✅ Destino `{d}` eliminado.", reply_markup=MAIN_KB)
        except:
            await update.message.reply_text("❌ Selección inválida.", reply_markup=MAIN_KB)
        context.user_data.pop("waiting_for")
        return

    if waiting == "new_list_name":
        context.user_data["new_list_name"] = text.strip()
        await update.message.reply_text("📋 Ahora envía los IDs separados por comas o líneas:", reply_markup=BACK_KB)
        context.user_data["waiting_for"] = "new_list_ids"
        return

    if waiting == "new_list_ids":
        name = context.user_data.pop("new_list_name")
        ids = [x.strip() for x in text.replace("\n", ",").split(",") if x.strip()]
        lists = cfg.setdefault("listas_destinos", {})
        lists[name] = ids
        save_config(cfg)
        await update.message.reply_text(f"✅ Lista `{name}` creada con {len(ids)} destinos.", reply_markup=MAIN_KB)
        context.user_data.pop("waiting_for")
        return

    if waiting == "manage_lists":
        if text == "🔙 Volver":
            await start(update, context)
        else:
            lists = cfg.get("listas_destinos", {})
            if text in lists:
                kb = ReplyKeyboardMarkup([["📋 Ver", "❌ Eliminar"], ["🔙 Volver"]], resize_keyboard=True)
                await update.message.reply_text(f"📂 *{text}* ({len(lists[text])} destinos)", parse_mode="Markdown", reply_markup=kb)
                context.user_data["waiting_for"] = f"list_{text}"
        return

    if waiting and waiting.startswith("list_"):
        name = waiting.split("_", 1)[1]
        if text == "📋 Ver":
            ids = cfg["listas_destinos"].get(name, [])
            await update.message.reply_text("\n".join(ids) or "Ninguno", reply_markup=MAIN_KB)
        elif text == "❌ Eliminar":
            cfg["listas_destinos"].pop(name, None)
            save_config(cfg)
            await update.message.reply_text(f"❌ Lista `{name}` eliminada.", reply_markup=MAIN_KB)
        else:
            await start(update, context)
        context.user_data.pop("waiting_for")
        return

    # ── 3) Nuevo mensaje reenviado desde origen ──
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

    # ── 4) Configuración de mensaje puntual ──
    if waiting and waiting.startswith("msg_cfg_"):
        idx = int(waiting.split("_")[-1])
        m = mensajes[idx]
        if text == "👥 A Todos":
            m["dest_all"], m["dest_list"] = True, None
            mensajes_manager.save_mensajes(mensajes)
            await update.message.reply_text("✅ Enviar a todos.", reply_markup=MAIN_KB)
            context.user_data.pop("waiting_for")
        elif text == "📋 Lista":
            lists = list(cfg.get("listas_destinos", {}).keys())
            if not lists:
                await update.message.reply_text("⚠️ No hay listas.", reply_markup=MAIN_KB)
                context.user_data.pop("waiting_for")
            else:
                kb = ReplyKeyboardMarkup([[n] for n in lists] + [["🔙 Volver"]], resize_keyboard=True)
                await update.message.reply_text("📋 Elige lista:", reply_markup=kb)
                context.user_data["waiting_for"] = f"msg_list_{idx}"
        elif text == "✅ Guardar":
            await update.message.reply_text("✅ Mensaje guardado.", reply_markup=MAIN_KB)
            context.user_data.pop("waiting_for")
        elif text == "❌ Cancelar":
            mensajes.pop(idx)
            mensajes_manager.save_mensajes(mensajes)
            await update.message.reply_text("❌ Mensaje descartado.", reply_markup=MAIN_KB)
            context.user_data.pop("waiting_for")
        elif text == "🏁 Finalizar":
            await update.message.reply_text("🏁 ¡Reenvío iniciado!", reply_markup=MAIN_KB)
            context.user_data.pop("waiting_for")
        return

    # ── 5) Editar Mensaje ──
    if text == "✏️ Editar Mensaje" and not waiting:
        if not mensajes:
            await update.message.reply_text("⚠️ No hay mensajes para editar.", reply_markup=MAIN_KB)
            return
        # página 0
        page_items, has_next = paginate_list(mensajes, 0, ITEMS_PER_PAGE)
        lines = "\n".join(f"{i+1}. {m['message_id']} ({m['intervalo_segundos']}s)" for i, m in enumerate(page_items))
        kb = ReplyKeyboardMarkup(
            [[str(i+1) for i in range(len(page_items))]] +
            ([["➡️ Siguiente"]] if has_next else []) +
            [["🔙 Volver"]], resize_keyboard=True
        )
        await update.message.reply_text(f"✏️ *Selecciona mensaje:* \n{lines}", parse_mode="Markdown", reply_markup=kb)
        context.user_data.update({"waiting_for": "edit_select", "edit_page": 0})
        return

    if waiting == "edit_select":
        page = context.user_data.get("edit_page", 0)
        items, has_next = paginate_list(mensajes, page, ITEMS_PER_PAGE)
        try:
            idx = int(text) - 1
            global_idx = page * ITEMS_PER_PAGE + idx
            context.user_data["edit_idx"] = global_idx
            kb = ReplyKeyboardMarkup(
                [["🕒 Cambiar Intervalo", "👥 Cambiar Destino"],
                 ["📋 Cambiar Lista", "🗑️ Eliminar Mensaje"],
                 ["🔙 Volver"]], resize_keyboard=True
            )
            await update.message.reply_text("✏️ ¿Qué deseas hacer?", reply_markup=kb)
            context.user_data["waiting_for"] = "edit_menu"
        except:
            if text == "➡️ Siguiente" and has_next:
                page += 1
                context.user_data["edit_page"] = page
                items, has_next = paginate_list(mensajes, page, ITEMS_PER_PAGE)
                lines = "\n".join(f"{i+1}. {m['message_id']} ({m['intervalo_segundos']}s)"
                                  for i, m in enumerate(items))
                kb = ReplyKeyboardMarkup(
                    [[str(i+1) for i in range(len(items))]] +
                    ([["➡️ Siguiente"]] if has_next else []) +
                    [["🔙 Volver"]], resize_keyboard=True
                )
                await update.message.reply_text(f"✏️ *Selecciona mensaje:* \n{lines}", parse_mode="Markdown", reply_markup=kb)
            else:
                await start(update, context)
        return

    # ... Aquí implementarías 'edit_menu', 'edit_interval', 'edit_dest_all', 'edit_list', etc.

    # ── 6) Eliminar Mensaje ──
    if text == "🗑️ Eliminar Mensaje" and not waiting:
        if not mensajes:
            await update.message.reply_text("⚠️ No hay mensajes para eliminar.", reply_markup=MAIN_KB)
            return
        lines = "\n".join(f"{i+1}. {m['message_id']}" for i, m in enumerate(mensajes))
        await update.message.reply_text("🗑️ Selecciona número para eliminar:\n" + lines, reply_markup=BACK_KB)
        context.user_data["waiting_for"] = "del_msg"
        return

    if waiting == "del_msg":
        try:
            idx = int(text) - 1
            m = mensajes.pop(idx)
            mensajes_manager.save_mensajes(mensajes)
            await update.message.reply_text(f"✅ Mensaje `{m['message_id']}` eliminado.", reply_markup=MAIN_KB)
        except:
            await update.message.reply_text("❌ Selección inválida.", reply_markup=MAIN_KB)
        context.user_data.pop("waiting_for")
        return

    # ── 7) Cambiar Intervalo ──
    if text == "🔁 Cambiar Intervalo" and not waiting:
        kb = ReplyKeyboardMarkup([
            ["🌐 Global", "📄 Por Mensaje"],
            ["📁 Por Lista"],
            ["🔙 Volver"]
        ], resize_keyboard=True)
        await update.message.reply_text("🔁 *Cambiar Intervalo*", parse_mode="Markdown", reply_markup=kb)
        context.user_data["waiting_for"] = "interval_menu"
        return

    # ... implementar sub-flujos de intervalo similar a anteriores ...

    # ── 8) Cambiar Zona Horaria ──
    if text == "🌐 Cambiar Zona" and not waiting:
        await update.message.reply_text("🌐 Envía la nueva zona (ej: Europe/Madrid):", reply_markup=BACK_KB)
        context.user_data["waiting_for"] = "change_zone"
        return

    if waiting == "change_zone":
        try:
            pytz.timezone(text)
            cfg["timezone"] = text
            save_config(cfg)
            await update.message.reply_text(f"✅ Zona cambiada a `{text}`.", parse_mode="Markdown", reply_markup=MAIN_KB)
        except Exception:
            await update.message.reply_text("❌ Zona inválida. Intenta de nuevo.", reply_markup=BACK_KB)
        context.user_data.pop("waiting_for")
        return

    # ── 9) Estado del Bot ──
    if text == "📄 Estado del Bot" and not waiting:
        await start(update, context)
        return

def get_handlers():
    """Devuelve la lista de handlers para registrar en main.py"""
    return [
        CommandHandler("start", start),
        MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler)
                ]
