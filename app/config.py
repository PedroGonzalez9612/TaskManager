import os


class Config:
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "taskmanager")
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"

    # Firma la cookie de sesión. En cualquier entorno compartido debe venir del .env.
    SECRET_KEY = os.environ.get("SECRET_KEY", "solo-para-desarrollo-cambiar")

    # Tamaño máximo de una petición (protege la subida del logo). El límite del logo es menor (512 KB).
    MAX_CONTENT_LENGTH = 1024 * 1024

    # Superadmin que se crea la primera vez que arranca el sistema (si aún no existe ninguno).
    SUPERADMIN_NOMBRE = os.environ.get("SUPERADMIN_NOMBRE", "Superadmin")
    SUPERADMIN_CORREO = os.environ.get("SUPERADMIN_CORREO")
    SUPERADMIN_CONTRASENA = os.environ.get("SUPERADMIN_CONTRASENA")
