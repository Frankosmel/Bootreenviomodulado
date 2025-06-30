# scheduler.py

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class Scheduler:
    def __init__(self, app, config, mensajes_manager):
        """
        :param app: instancia de telegram.ext.Application
        :param config: dict de config.json
        :param mensajes_manager: módulo mensajes_manager (con load/save)
        """
        tz = pytz.timezone(config.get("timezone", "UTC"))
        self.scheduler = AsyncIOScheduler(timezone=tz)
        self.app = app
        self.config = config
        self.mensajes_manager = mensajes_manager

    def start(self):
        """
        Programa y arranca el job de reenvío periódico.
        Debe llamarse *dentro* de un event loop ya en marcha.
        """
        interval = self.config.get("intervalo_segundos", 60)
        # Job que llama a _run_forwarder cada `interval` segundos
        self.scheduler.add_job(self._run_forwarder, "interval", seconds=interval, id="forward_job")
        self.scheduler.start()

    async def _run_forwarder(self):
        """
        Recupera los mensajes programados y los reenvía.
        Se ejecuta en el event loop de asyncio.
        """
        from forwarder import Forwarder  # import aquí para evitar ciclos
        mensajes = self.mensajes_manager.load_mensajes()
        f = Forwarder(self.app, self.config, mensajes)
        await f.reenviar_todos()
