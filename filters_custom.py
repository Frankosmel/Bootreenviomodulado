from telegram.ext import filters
from config_manager import load_config

class FilterForwardedFromOrigin(filters.MessageFilter):
    def filter(self, message):
        origin = load_config().get("origen_chat_id")
        if message.forward_from_chat:
            return str(message.forward_from_chat.id) == str(origin)
        return False
