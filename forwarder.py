class Forwarder:
    def __init__(self, app, config, mensajes):
        self.bot = app.bot
        self.config = config
        self.mensajes = mensajes

    async def reenviar_todos(self):
        for m in self.mensajes:
            dests = self.config['destinos'] if m['dest_all'] else self.config['listas_destinos'].get(m['dest_list'], [])
            for d in dests:
                try:
                    await self.bot.forward_message(chat_id=d, from_chat_id=m['from_chat_id'], message_id=m['message_id'])
                except Exception as e:
                    print(f"Error al reenviar {m['message_id']} a {d}: {e}")
