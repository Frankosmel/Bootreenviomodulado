#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class Scheduler:
    def __init__(self, app, config, mensajes_manager):
        """
        :param app: instancia de telegram.ext.Application
        :param config: dict cargado de config.json
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
        Debe llamarse dentro del event loop (usamos post_init en main.py).
        """
        interval = self.config.get("intervalo_segundos", 60)
        self.scheduler.add_job(
            self._run_forwarder,
            "interval",
            seconds=interval,
            id="forward_job",
            replace_existing=True
        )
        self.scheduler.start()

    async def _run_forwarder(self):
        """
        Recupera los mensajes programados y los reenvía.
        Se ejecuta en el mismo event loop de asyncio.
        """
        from forwarder import Forwarder  # import dinámico para evitar ciclos
        mensajes = self.mensajes_manager.load_mensajes()
        f = Forwarder(self.app, self.config, mensajes)
        await f.reenviar_todos()
