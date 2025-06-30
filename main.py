#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Application
from logger_config import setup_logging
from config_manager import load_config
import mensajes_manager       # Importamos el módulo completo
from handlers import get_handlers
from scheduler import Scheduler

def main():
    # 1) Logging
    setup_logging()

    # 2) Carga de config y mensajes
    cfg = load_config()
    msgs_mgr = mensajes_manager  # PASAMOS el módulo, no la lista

    # 3) Callback para arrancar el scheduler dentro del event loop
    async def on_startup(app):
        sched = Scheduler(app, cfg, msgs_mgr)
        sched.start()

    # 4) Construcción de la aplicación
    app = (
        Application.builder()
        .token(cfg["bot_token"])
        .post_init(on_startup)
        .build()
    )

    # 5) Registramos handlers
    for h in get_handlers():
        app.add_handler(h)

    # 6) Arrancamos polling (levanta el loop)
    app.run_polling()

if __name__ == "__main__":
    main()
