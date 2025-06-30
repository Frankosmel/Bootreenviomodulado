import logging

def setup_logging():
    """
    Configura el logging para toda la aplicación:
    - Formato estándar con fecha, módulo y nivel.
    - Nivel INFO por defecto.
    - Reduce el ruido de APScheduler.
    """
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    # Opcional: silenciar logs muy verbosos de APScheduler
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
