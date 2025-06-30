#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Application
from logger_config import setup_logging
from config_manager import load_config
import mensajes_manager      # Importa el módulo, no su función
from handlers import get_handlers
from scheduler import Scheduler

def main():
    setup_logging()

    cfg = load_config()
    # Aquí pasamos el módulo, no la lista
    msgs_mgr = mensajes_manager

    async def on_startup(app):
        sched = Scheduler(app, cfg, msgs_mgr)
        sched.start()

    app = (
        Application.builder()
        .token(cfg["bot_token"])
        .post_init(on_startup)
        .build()
    )

    for h in get_handlers():
        app.add_handler(h)

    app.run_polling()

if __name__ == "__main__":
    main()
