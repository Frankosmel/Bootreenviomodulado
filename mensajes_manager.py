import json, os

MENSAJES_FILE = "mensajes.json"

# Estructura esperada de cada mensaje:
# {
#   "from_chat_id": int,
#   "message_id": int,
#   "intervalo_segundos": int,
#   "dest_all": bool,
#   "dest_list": Optional[str],
#   "timestamp": str  # ISO format al crear
# }

def load_mensajes() -> list:
    """
    Carga la lista de mensajes programados desde mensajes.json.
    Si el archivo no existe, lo crea con una lista vacía.
    Si está corrupto, lo resetea.
    Retorna la lista de mensajes.
    """
    if not os.path.exists(MENSAJES_FILE):
        with open(MENSAJES_FILE, "w") as f:
            json.dump([], f, indent=4)
        return []

    try:
        with open(MENSAJES_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # En caso de corrupción o error de lectura, resetear
        with open(MENSAJES_FILE, "w") as f:
            json.dump([], f, indent=4)
        return []


def save_mensajes(msgs: list) -> None:
    """
    Guarda la lista de mensajes en mensajes.json con indentación.
    """
    with open(MENSAJES_FILE, "w") as f:
        json.dump(msgs, f, indent=4)
