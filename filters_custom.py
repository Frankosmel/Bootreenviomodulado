from telegram.ext import filters
from config_manager import load_config

class FilterForwardedFromOrigin(filters.MessageFilter):
    """
    Filtra mensajes reenviados desde el canal de origen configurado en config.json.
    """
    def filter(self, message):
        cfg = load_config()
        origin_id = cfg.get("origen_chat_id")
        # Si no hay canal de origen configurado, no pasa filter
        if not origin_id:
            return False
        fchat = getattr(message, 'forward_from_chat', None)
        return bool(fchat and str(fchat.id) == str(origin_id))

# Instancia para usar en handlers:
filter_forwarded_from_origin = FilterForwardedFromOrigin()
