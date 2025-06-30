om telegram.ext import Application
from config_manager import load_config
from mensajes_manager import load_mensajes
from logger_config import setup_logging
from handlers import get_handlers
from scheduler import Scheduler


def main():
    setup_logging()
    config = load_config()
    mensajes_mgr = load_mensajes()
    app = Application.builder().token(config['bot_token']).build()

    for handler in get_handlers():
        app.add_handler(handler)

    sched = Scheduler(app, config, mensajes_mgr)
    sched.start()

    app.run_polling()

if __name__ == "__main__":
    main()
