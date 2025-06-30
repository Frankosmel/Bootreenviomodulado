#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Forwarder:
    def __init__(self, app, config, mensajes):
        """
        :param app: instancia de Application
        :param config: dict con config.json
        :param mensajes: lista de mensajes programados
        """
        self.bot = app.bot
        self.config = config
        self.mensajes = mensajes

    async def reenviar_todos(self):
        """
        Itera sobre cada mensaje programado y lo reenvía
        o bien a 'destinos' o bien a la lista cfg['listas_destinos'][dest_list].
        """
        for m in self.mensajes:
            if m.get("dest_all", True):
                dests = self.config.get("destinos", [])
            else:
                dests = self.config.get("listas_destinos", {}).get(m.get("dest_list"), [])
            for d in dests:
                try:
                    await self.bot.forward_message(
                        chat_id=d,
                        from_chat_id=m["from_chat_id"],
                        message_id=m["message_id"]
                    )
                    print(f"✔️ {m['message_id']} → {d}")
                except Exception as e:
                    print(f"❌ {m['message_id']} → {d}: {e}")
