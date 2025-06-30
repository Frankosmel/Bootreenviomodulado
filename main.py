# main.py

from telegram.ext import Application
from logger_config import setup_logging
from config_manager import load_config
from mensajes_manager import load_mensajes
from handlers import get_handlers
from scheduler import Scheduler

def main():
    # 1) Logging
    setup_logging()

    # 2) Carga configuración y mensajes
    config = load_config()
    mensajes_mgr = load_mensajes()

    # 3) Define función de startup para arrancar el scheduler dentro del loop
    async def on_startup(application):
        sched = Scheduler(application, config, mensajes_mgr)
        sched.start()

    # 4) Construye la aplicación, inyectando el on_startup
    app = (
        Application.builder()
        .token(config["bot_token"])
        .post_init(on_startup)  # se ejecuta cuando el loop ya está corriendo
        .build()
    )

    # 5) Registra todos los handlers
    for handler in get_handlers():
        app.add_handler(handler)

    # 6) Arranca el polling (esto levanta el event loop)
    app.run_polling()

if __name__ == "__main__":
    main()
