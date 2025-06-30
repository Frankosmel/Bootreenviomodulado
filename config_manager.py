import json, os

CONFIG_FILE = "config.json"
# Valores por defecto para la configuración inicial
default_config = {
    "bot_token": "",
    "admin_id": 0,
    "origen_chat_id": "",
    "destinos": [],
    "listas_destinos": {},
    "intervalo_segundos": 60,
    "horario": {"activo": False, "inicio": "00:00", "fin": "23:59"},
    "timezone": "UTC"
}

def load_config():
    """
    Carga el archivo config.json. Si no existe o faltan claves,
    crea/configura con default_config.
    """
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config.copy()

    with open(CONFIG_FILE, "r") as f:
        try:
            cfg = json.load(f)
        except json.JSONDecodeError:
            cfg = {}

    # Asegura que todas las claves estén presentes
    updated = False
    for key, val in default_config.items():
        if key not in cfg:
            cfg[key] = val
            updated = True
    if updated:
        save_config(cfg)

    return cfg


def save_config(conf: dict):
    """
    Guarda la configuración en config.json, respetando indentación.
    """
    with open(CONFIG_FILE, "w") as f:
        json.dump(conf, f, indent=4)
