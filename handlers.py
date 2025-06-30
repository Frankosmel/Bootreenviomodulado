#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, MessageHandler, filters
)
from telegram.error import BadRequest
from decorators import admin_only, log_exceptions
from keyboards import MAIN_KB, BACK_KB
from config_manager import load_config, save_config
import mensajes_manager
from filters_custom import filter_forwarded_from_origin
from pagination import paginate_list
from datetime import datetime
import pytz

ITEMS_PER_PAGE = 3

@admin_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start → muestra el menú principal con estado actual y limpia estados.
    """
    cfg = load_config()
    mens = mensajes_manager.load_mensajes()
    text = (
        "🚀 *Menú Principal*\n\n"
        f"📺 Canal Origen: `{cfg.get('origen_chat_id','No asignado')}`\n"
        f"👥 Destinos: {len(cfg.get('destinos',[]))}\n"
        f"📁 Listas Destinos: {len(cfg.get('listas_destinos',{}))}\n"
        f"📨 Mensajes Configurados: {len(mens)}\n"
        f"⏱️ Intervalo Global: {cfg.get('intervalo_segundos',60)}s\n"
        f"🌐 Zona Horaria: `{cfg.get('timezone','UTC')}`\n\n"
        "Selecciona una opción:"
    )
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=MAIN_KB
    )
    context.user_data.clear()

@admin_only
@log_exceptions
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler global: controla todos los flujos según context.user_data['waiting_for'].
    """
    cfg = load_config()
    mens = mensajes_manager.load_mensajes()
    text = update.message.text or ""
    waiting = context.user_data.get("waiting_for")

    # ── 1) Configurar Canal Origen por ID ──
    if text == "🖊️ Configurar Canal ID" and not waiting:
        await update.message.reply_text(
            "🖊️ *Envía el ID* de tu canal de origen (p.e. `-1001234567890`):",
            parse_mode="Markdown", reply_markup=BACK_KB
        )
        context.user_data["waiting_for"] = "set_origin_id"
        return

    if waiting == "set_origin_id":
        cid = text.strip()
        try:
            int(cid)
            chat = await update.effective_bot.get_chat(cid)
            title = chat.title or "<sin título>"
            username = f"@{chat.username}" if chat.username else ""
            cfg["origen_chat_id"] = cid
            save_config(cfg)
            await update.message.reply_text(
                f"✅ Canal configurado:\n"
                f"• ID: `{cid}`\n"
                f"• Título: *{title}*\n"
                f"• Usuario: `{username}`\n\n"
                "Asegúrate de que el bot sea administrador con permisos de lectura.",
                parse_mode="Markdown", reply_markup=MAIN_KB
            )
        except ValueError:
            await update.message.reply_text(
                "❌ ID inválido. Debe ser un número (p.e. `-1001234567890`).",
                parse_mode="Markdown", reply_markup=BACK_KB
            )
        except BadRequest as e:
            await update.message.reply_text(
                f"❌ No pude acceder al chat: {e.message}\n"
                "Verifica que el bot esté agregado y sea admin.",
                reply_markup=BACK_KB
            )
        context.user_data.pop("waiting_for", None)
        return

    # ── 2) Gestión de Destinos ──
    if text == "📂 Destinos" and not waiting:
        kb = ReplyKeyboardMarkup([
            ["➕ Agregar Destino", "🗑️ Eliminar Destino"],
            ["📁 Crear Lista",       "📂 Gestionar Listas"],
            ["🔙 Volver"]
        ], resize_keyboard=True)
        await update.message.reply_text(
            "📂 *Gestión de Destinos*", parse_mode="Markdown", reply_markup=kb
        )
        context.user_data["waiting_for"] = "destinos_menu"
        return

    # Sub-flujos de destinos
    if waiting == "destinos_menu":
        if text == "➕ Agregar Destino":
            await update.message.reply_text("📝 Envía el ID del destino:", reply_markup=BACK_KB)
            context.user_data["waiting_for"] = "add_destino"
        elif text == "🗑️ Eliminar Destino":
            ds = cfg.get("destinos", [])
            if not ds:
                await update.message.reply_text("⚠️ No hay destinos.", reply_markup=MAIN_KB)
                context.user_data.pop("waiting_for")
            else:
                lines = "\n".join(f"{i+1}. {d}" for i,d in enumerate(ds))
                await update.message.reply_text(f"🗑️ Selecciona número para eliminar:\n{lines}", reply_markup=BACK_KB)
                context.user_data["waiting_for"] = "del_destino"
        elif text == "📁 Crear Lista":
            await update.message.reply_text("📌 Nombre de la nueva lista:", reply_markup=BACK_KB)
            context.user_data["waiting_for"] = "new_list_name"
        elif text == "📂 Gestionar Listas":
            lists = cfg.get("listas_destinos", {})
            if not lists:
                await update.message.reply_text("⚠️ No hay listas.", reply_markup=MAIN_KB)
                context.user_data.pop("waiting_for")
            else:
                menu = [[n] for n in lists] + [["🔙 Volver"]]
                await update.message.reply_text(
                    "📂 *Listas Disponibles:*", parse_mode="Markdown",
                    reply_markup=ReplyKeyboardMarkup(menu, resize_keyboard=True)
                )
                context.user_data["waiting_for"] = "manage_lists"
        elif text == "🔙 Volver":
            await start(update, context)
        return

    if waiting == "add_destino":
        d = text.strip()
        lst = cfg.setdefault("destinos", [])
        if d and d not in lst:
            lst.append(d); save_config(cfg)
            await update.message.reply_text(f"✅ Destino `{d}` agregado.", reply_markup=MAIN_KB)
        else:
            await update.message.reply_text("⚠️ ID inválido o ya existe.", reply_markup=MAIN_KB)
        context.user_data.pop("waiting_for")
        return

    if waiting == "del_destino":
        try:
            idx = int(text)-1
            d = cfg["destinos"].pop(idx); save_config(cfg)
            await update.message.reply_text(f"✅ Destino `{d}` eliminado.", reply_markup=MAIN_KB)
        except:
            await update.message.reply_text("❌ Selección inválida.", reply_markup=MAIN_KB)
        context.user_data.pop("waiting_for")
        return

    if waiting == "new_list_name":
        context.user_data["new_list_name"] = text.strip()
        await update.message.reply_text("📋 Envía los IDs separados por comas o líneas:", reply_markup=BACK_KB)
        context.user_data["waiting_for"] = "new_list_ids"
        return

    if waiting == "new_list_ids":
        name = context.user_data.pop("new_list_name")
        ids = [x.strip() for x in text.replace("\n",",").split(",") if x.strip()]
        lists = cfg.setdefault("listas_destinos", {}); lists[name] = ids; save_config(cfg)
        await update.message.reply_text(f"✅ Lista `{name}` creada con {len(ids)} destinos.", reply_markup=MAIN_KB)
        context.user_data.pop("waiting_for")
        return

    if waiting == "manage_lists":
        if text == "🔙 Volver":
            await start(update, context)
        else:
            lists = cfg.get("listas_destinos", {})
            if text in lists:
                kb = ReplyKeyboardMarkup([["📋 Ver","❌ Eliminar"],["🔙 Volver"]], resize_keyboard=True)
                await update.message.reply_text(
                    f"📂 *{text}* ({len(lists[text])} destinos)",
                    parse_mode="Markdown", reply_markup=kb
                )
                context.user_data["waiting_for"] = f"list_{text}"
        return

    if waiting and waiting.startswith("list_"):
        name = waiting.split("_",1)[1]
        if text == "📋 Ver":
            items = cfg["listas_destinos"].get(name, [])
            await update.message.reply_text("\n".join(items) or "Ninguno", reply_markup=MAIN_KB)
        elif text == "❌ Eliminar":
            cfg["listas_destinos"].pop(name, None); save_config(cfg)
            await update.message.reply_text(f"❌ Lista `{name}` eliminada.", reply_markup=MAIN_KB)
        else:
            await start(update, context)
        context.user_data.pop("waiting_for")
        return

    # ── 3) Configuración de Mensajes a reenviar ──
    if filter_forwarded_from_origin.filter(update.message) and not waiting:
        mid = update.message.forward_from_message_id
        nuevo = {
            "from_chat_id": update.message.forward_from_chat.id,
            "message_id": mid,
            "intervalo_segundos": cfg.get("intervalo_segundos",60),
            "dest_all": True,
            "dest_list": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        mens.append(nuevo); mensajes_manager.save_mensajes(mens)
        kb = ReplyKeyboardMarkup([
            ["👥 A Todos","📋 Lista"],
            ["✅ Guardar","❌ Cancelar"],
            ["🏁 Finalizar"],["🔙 Volver"]
        ], resize_keyboard=True)
        await update.message.reply_text(
            f"🔥 *Nuevo Mensaje ({mid})*\nIntervalo: `{nuevo['intervalo_segundos']}s`\nElige destino:",
            parse_mode="Markdown", reply_markup=kb
        )
        context.user_data["waiting_for"] = f"msg_cfg_{len(mens)-1}"
        return

    # ── 4) Flujos de Configuración puntual ──
    if waiting and waiting.startswith("msg_cfg_"):
        idx = int(waiting.split("_")[-1])
        m = mens[idx]
        if text == "👥 A Todos":
            m["dest_all"], m["dest_list"] = True, None
            mensajes_manager.save_mensajes(mens)
            await update.message.reply_text("✅ Enviar a todos.", reply_markup=MAIN_KB)
            context.user_data.pop("waiting_for")
        elif text == "📋 Lista":
            lists = list(cfg.get("listas_destinos",{}).keys())
            if not lists:
                await update.message.reply_text("⚠️ No hay listas.", reply_markup=MAIN_KB)
                context.user_data.pop("waiting_for")
            else:
                kb = [[n] for n in lists] + [["🔙 Volver"]]
                await update.message.reply_text("📋 Elige lista:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
                context.user_data["waiting_for"] = f"msg_list_{idx}"
        elif text == "✅ Guardar":
            await update.message.reply_text("✅ Mensaje guardado.", reply_markup=MAIN_KB)
            context.user_data.pop("waiting_for")
        elif text == "❌ Cancelar":
            mens.pop(idx); mensajes_manager.save_mensajes(mens)
            await update.message.reply_text("❌ Mensaje descartado.", reply_markup=MAIN_KB)
            context.user_data.pop("waiting_for")
        elif text == "🏁 Finalizar":
            await update.message.reply_text("🏁 ¡Reenvío iniciado!", reply_markup=MAIN_KB)
            context.user_data.pop("waiting_for")
        elif text == "🔙 Volver":
            await start(update, context); context.user_data.pop("waiting_for")
        return

    if waiting and waiting.startswith("msg_list_"):
        idx = int(waiting.split("_")[-1])
        lists = cfg.get("listas_destinos",{})
        if text in lists:
            m = mens[idx]
            m["dest_all"], m["dest_list"] = False, text
            mensajes_manager.save_mensajes(mens)
            await update.message.reply_text(f"✅ Enviar a lista `{text}`.", reply_markup=MAIN_KB)
        else:
            await update.message.reply_text("🔙 Cancelado.", reply_markup=MAIN_KB)
        context.user_data.pop("waiting_for")
        return

    # ── 5) Editar Mensaje ──
    if text == "✏️ Editar Mensaje" and not waiting:
        if not mens:
            await update.message.reply_text("⚠️ No hay mensajes para editar.", reply_markup=MAIN_KB)
            return
        page_items, has_next = paginate_list(mens, 0, ITEMS_PER_PAGE)
        lines = "\n".join(f"{i+1}. {m['message_id']} ({m['intervalo_segundos']}s)" for i,m in enumerate(page_items))
        kb = [[str(i+1) for i in range(len(page_items))]]
        if has_next: kb.append(["➡️ Siguiente"])
        kb.append(["🔙 Volver"])
        await update.message.reply_text(
            f"✏️ *Selecciona mensaje:*\n{lines}",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        context.user_data.update({"waiting_for":"edit_select","edit_page":0})
        return

    if waiting == "edit_select":
        page = context.user_data.get("edit_page",0)
        items, has_next = paginate_list(mens,page,ITEMS_PER_PAGE)
        try:
            idx = int(text)-1
            global_idx = page*ITEMS_PER_PAGE+idx
            context.user_data["edit_idx"] = global_idx
            kb = ReplyKeyboardMarkup([
                ["🕒 Cambiar Intervalo","👥 Cambiar Destino"],
                ["📋 Cambiar Lista","🗑️ Eliminar Mensaje"],
                ["🔙 Volver"]
            ], resize_keyboard=True)
            await update.message.reply_text("✏️ ¿Qué deseas hacer?", reply_markup=kb)
            context.user_data["waiting_for"] = "edit_menu"
        except:
            if text=="➡️ Siguiente" and has_next:
                page+=1; context.user_data["edit_page"]=page
                items, has_next = paginate_list(mens,page,ITEMS_PER_PAGE)
                lines = "\n".join(f"{i+1}. {m['message_id']} ({m['intervalo_segundos']}s)" for i,m in enumerate(items))
                kb = [[str(i+1) for i in range(len(items))]]
                if has_next: kb.append(["➡️ Siguiente"])
                kb.append(["🔙 Volver"])
                await update.message.reply_text(
                    f"✏️ *Selecciona mensaje:*\n{lines}",
                    parse_mode="Markdown",
                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
                )
            else:
                await start(update, context)
        return

    if waiting == "edit_menu":
        idx = context.user_data.get("edit_idx")
        m = mens[idx]
        if text == "🕒 Cambiar Intervalo":
            await update.message.reply_text("🕒 Envía nuevo intervalo (s):", reply_markup=BACK_KB)
            context.user_data["waiting_for"] = "edit_interval"
        elif text == "🗑️ Eliminar Mensaje":
            mens.pop(idx); mensajes_manager.save_mensajes(mens)
            await update.message.reply_text("✅ Mensaje eliminado.", reply_markup=MAIN_KB)
            context.user_data.pop("waiting_for")
        elif text == "👥 Cambiar Destino":
            await update.message.reply_text(
                "👥 ¿Enviar a todos o lista?",
                reply_markup=ReplyKeyboardMarkup([["👥 A Todos","📋 Lista"],["🔙 Volver"]], resize_keyboard=True)
            )
            context.user_data["waiting_for"] = "edit_choose_dest"
        elif text == "📋 Cambiar Lista":
            lists = list(cfg.get("listas_destinos",{}).keys())
            if not lists:
                await update.message.reply_text("⚠️ No hay listas.", reply_markup=MAIN_KB)
                context.user_data.pop("waiting_for")
            else:
                kb = [[n] for n in lists] + [["🔙 Volver"]]
                await update.message.reply_text("📋 Elige lista:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
                context.user_data["waiting_for"] = "edit_list_idx"
        elif text == "🔙 Volver":
            await start(update, context); context.user_data.pop("waiting_for")
        return

    if waiting == "edit_interval":
        try:
            iv = int(text)
            idx = context.user_data.get("edit_idx")
            mens[idx]["intervalo_segundos"] = iv
            mensajes_manager.save_mensajes(mens)
            await update.message.reply_text(f"✅ Intervalo actualizado a {iv}s.", reply_markup=MAIN_KB)
        except:
            await update.message.reply_text("❌ Valor inválido.", reply_markup=MAIN_KB)
        context.user_data.pop("waiting_for")
        return

    if waiting == "edit_choose_dest":
        idx = context.user_data.get("edit_idx")
        if text == "👥 A Todos":
            mens[idx].update({"dest_all":True,"dest_list":None})
            mensajes_manager.save_mensajes(mens)
            await update.message.reply_text("✅ Se reenviará a todos.", reply_markup=MAIN_KB)
            context.user_data.pop("waiting_for")
        elif text == "📋 Lista":
            lists = list(cfg.get("listas_destinos",{}).keys())
            if not lists:
                await update.message.reply_text("⚠️ No hay listas.", reply_markup=MAIN_KB)
                context.user_data.pop("waiting_for")
            else:
                kb = [[n] for n in lists] + [["🔙 Volver"]]
                await update.message.reply_text("📋 Elige lista:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
                context.user_data["waiting_for"] = "edit_list_idx"
        else:
            await start(update, context); context.user_data.pop("waiting_for")
        return

    if waiting == "edit_list_idx":
        idx = context.user_data.get("edit_idx")
        lists = cfg.get("listas_destinos",{})
        if text in lists:
            mens[idx].update({"dest_all":False,"dest_list":text})
            mensajes_manager.save_mensajes(mens)
            await update.message.reply_text(f"✅ Destino cambiado a lista `{text}`.", reply_markup=MAIN_KB)
        else:
            await update.message.reply_text("🔙 Cancelado.", reply_markup=MAIN_KB)
        context.user_data.pop("waiting_for")
        return

    # ── 6) Eliminar Mensaje rápido ──
    if text == "🗑️ Eliminar Mensaje" and not waiting:
        if not mens:
            await update.message.reply_text("⚠️ No hay mensajes para eliminar.", reply_markup=MAIN_KB)
            return
        lines = "\n".join(f"{i+1}. {m['message_id']}" for i,m in enumerate(mens))
        await update.message.reply_text(f"🗑️ Selecciona número para eliminar:\n{lines}", reply_markup=BACK_KB)
        context.user_data["waiting_for"] = "del_msg"
        return

    if waiting == "del_msg":
        try:
            idx = int(text)-1
            m = mens.pop(idx); mensajes_manager.save_mensajes(mens)
            await update.message.reply_text(f"✅ Mensaje `{m['message_id']}` eliminado.", reply_markup=MAIN_KB)
        except:
            await update.message.reply_text("❌ Selección inválida.", reply_markup=MAIN_KB)
        context.user_data.pop("waiting_for")
        return

    # ── 7) Cambiar Intervalo ──
    if text == "🔁 Cambiar Intervalo" and not waiting:
        kb = ReplyKeyboardMarkup([
            ["🌐 Global","📄 Por Mensaje"],
            ["📁 Por Lista"],["🔙 Volver"]
        ], resize_keyboard=True)
        await update.message.reply_text("🔁 *Cambiar Intervalo*", parse_mode="Markdown", reply_markup=kb)
        context.user_data["waiting_for"] = "interval_menu"
        return

    if waiting == "interval_menu":
        if text == "🌐 Global":
            await update.message.reply_text("⏱️ Envía nuevo intervalo global (s):", reply_markup=BACK_KB)
            context.user_data["waiting_for"] = "interval_global"
        elif text == "📄 Por Mensaje":
            if not mens:
                await update.message.reply_text("⚠️ No hay mensajes.", reply_markup=MAIN_KB)
                context.user_data.pop("waiting_for")
            else:
                page_items, has_next = paginate_list(mens,0,ITEMS_PER_PAGE)
                lines = "\n".join(f"{i+1}. {m['message_id']} ({m['intervalo_segundos']}s)" for i,m in enumerate(page_items))
                kb = [[str(i+1) for i in range(len(page_items))]]
                if has_next: kb.append(["➡️ Siguiente"])
                kb.append(["🔙 Volver"])
                await update.message.reply_text(
                    f"📄 *Selecciona mensaje:*\n{lines}",
                    parse_mode="Markdown",
                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
                )
                context.user_data.update({"waiting_for":"interval_select","interval_page":0})
        elif text=="📁 Por Lista":
            lists = list(cfg.get("listas_destinos",{}).keys())
            if not lists:
                await update.message.reply_text("⚠️ No hay listas.", reply_markup=MAIN_KB)
                context.user_data.pop("waiting_for")
            else:
                kb = [[n] for n in lists]+[["🔙 Volver"]]
                await update.message.reply_text("📁 Elige lista:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
                context.user_data["waiting_for"]="interval_list"
        elif text=="🔙 Volver":
            await start(update, context); context.user_data.pop("waiting_for")
        return

    if waiting=="interval_global":
        try:
            iv=int(text); cfg["intervalo_segundos"]=iv; save_config(cfg)
            await update.message.reply_text(f"✅ Intervalo global actualizado a {iv}s.", reply_markup=MAIN_KB)
        except:
            await update.message.reply_text("❌ Valor inválido.", reply_markup=MAIN_KB)
        context.user_data.pop("waiting_for"); return

    if waiting=="interval_select":
        page=context.user_data.get("interval_page",0)
        items, has_next = paginate_list(mens,page,ITEMS_PER_PAGE)
        try:
            idx=int(text)-1; global_idx=page*ITEMS_PER_PAGE+idx
            context.user_data["interval_msg_idx"]=global_idx
            await update.message.reply_text("⏱️ Envía nuevo intervalo (s):", reply_markup=BACK_KB)
            context.user_data["waiting_for"]="interval_msg_value"
        except:
            if text=="➡️ Siguiente" and has_next:
                page+=1; context.user_data["interval_page"]=page
                items, has_next=paginate_list(mens,page,ITEMS_PER_PAGE)
                lines="\n".join(f"{i+1}. {m['message_id']} ({m['intervalo_segundos']}s)" for i,m in enumerate(items))
                kb=[[str(i+1) for i in range(len(items))]]
                if has_next: kb.append(["➡️ Siguiente"])
                kb.append(["🔙 Volver"])
                await update.message.reply_text(
                    f"📄 *Selecciona mensaje:*\n{lines}",
                    parse_mode="Markdown",
                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
                )
            else:
                await start(update, context)
        return

    if waiting=="interval_msg_value":
        try:
            iv=int(text); idx=context.user_data.get("interval_msg_idx")
            mens[idx]["intervalo_segundos"]=iv; mensajes_manager.save_mensajes(mens)
            await update.message.reply_text(f"✅ Intervalo del mensaje actualizado a {iv}s.", reply_markup=MAIN_KB)
        except:
            await update.message.reply_text("❌ Valor inválido.", reply_markup=MAIN_KB)
        context.user_data.pop("waiting_for"); return

    if waiting=="interval_list":
        lists=cfg.get("listas_destinos",{})
        if text in lists:
            context.user_data["interval_list_name"]=text
            await update.message.reply_text(f"⏱️ Envía nuevo intervalo (s) para lista `{text}`:", reply_markup=BACK_KB)
            context.user_data["waiting_for"]="interval_list_value"
        else:
            await start(update, context); context.user_data.pop("waiting_for")
        return

    if waiting=="interval_list_value":
        try:
            iv=int(text); lname=context.user_data.get("interval_list_name")
            for m in mens:
                if m.get("dest_list")==lname:
                    m["intervalo_segundos"]=iv
            mensajes_manager.save_mensajes(mens)
            await update.message.reply_text(f"✅ Intervalo de lista `{lname}` actualizado a {iv}s.", reply_markup=MAIN_KB)
        except:
            await update.message.reply_text("❌ Valor inválido.", reply_markup=MAIN_KB)
        context.user_data.pop("waiting_for"); return

    # ── 8) Cambiar Zona Horaria ──
    if text=="🌐 Cambiar Zona" and not waiting:
        await update.message.reply_text("🌐 Envía la nueva zona (ej: Europe/Madrid):", reply_markup=BACK_KB)
        context.user_data["waiting_for"]="change_zone"
        return

    if waiting=="change_zone":
        try:
            pytz.timezone(text)
            cfg["timezone"]=text; save_config(cfg)
            await update.message.reply_text(f"✅ Zona cambiada a `{text}`.", parse_mode="Markdown", reply_markup=MAIN_KB)
        except:
            await update.message.reply_text("❌ Zona inválida.", reply_markup=BACK_KB)
        context.user_data.pop("waiting_for"); return

    # ── 9) Estado del Bot ──
    if text=="📄 Estado del Bot" and not waiting:
        await start(update, context); return

    # Opción no reconocida
    await update.message.reply_text("🤖 Opción no reconocida. Usa /start.", reply_markup=MAIN_KB)


def get_handlers():
    """Devuelve la lista de handlers para registrar en main.py"""
    return [
        CommandHandler("start", start),
        MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler)
    ]
