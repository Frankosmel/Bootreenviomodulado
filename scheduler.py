#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class Scheduler:
    def __init__(self, app, config, mensajes_manager):
        """
        Recibe el módulo mensajes_manager (no la lista).
        """
        tz = pytz.timezone(config.get("timezone", "UTC"))
        self.scheduler = AsyncIOScheduler(timezone=tz)
        self.app = app
        self.config = config
        self.mensajes_manager = mensajes_manager

    def start(self):
        interval = self.config.get("intervalo_segundos", 60)
        self.scheduler.add_job(
            self._run_forwarder,
            "interval",
            seconds=interval,
            id="forward_job",
            replace_existing=True
        )
        # Ahora sí hay un event loop corriendo (post_init)
        self.scheduler.start()

    async def _run_forwarder(self):
        from forwarder import Forwarder
        # load_mensajes() nos devuelve la lista actualizada
        mensajes = self.mensajes_manager.load_mensajes()
        f = Forwarder(self.app, self.config, mensajes)
        await f.reenviar_todos()
