#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Application
from logger_config import setup_logging
from config_manager import load_config
from mensajes_manager import load_mensajes
from handlers import get_handlers
from scheduler import Scheduler

def main():
    # 1) Configurar logging
    setup_logging()

    # 2) Cargar configuración y mensajes
    config = load_config()
    mensajes_mgr = load_mensajes()

    # 3) Definir callback para arrancar el scheduler dentro del event loop
    async def on_startup(application):
        sched = Scheduler(application, config, mensajes_mgr)
        sched.start()

    # 4) Construir la aplicación y registrar el callback
    app = (
        Application.builder()
        .token(config["bot_token"])
        .post_init(on_startup)
        .build()
    )

    # 5) Registrar handlers
    for handler in get_handlers():
        app.add_handler(handler)

    # 6) Iniciar polling (esto levanta el event loop)
    app.run_polling()

if __name__ == "__main__":
    main()
