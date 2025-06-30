import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class Scheduler:
    def __init__(self, app, config, mensajes_manager):
        tz = pytz.timezone(config.get("timezone", "UTC"))
        self.scheduler = AsyncIOScheduler(timezone=tz)
        self.app = app
        self.config = config
        self.mensajes_manager = mensajes_manager

    def start(self):
        interval = self.config.get("intervalo_segundos", 60)
        self.scheduler.add_job(self._run_forwarder, 'interval', seconds=interval, id='forward_job')
        self.scheduler.start()

    async def _run_forwarder(self):
        from forwarder import Forwarder
        msgs = self.mensajes_manager.load_mensajes()
        f = Forwarder(self.app, self.config, msgs)
        await f.reenviar_todos()
