"""Migración de las categorías de actividad a categorías generales (2026-10-16).

Las cinco categorías anteriores eran de una planta industrial. Las nuevas sirven para cualquier
empresa (alcance, Sección 5.1). Equivalencias:
    PRODUCCION, MANTENIMIENTO y LIMPIEZA -> OPERACION
    CALIDAD -> REVISION
    LOGISTICA -> TRASLADO

Se ejecuta a mano, una vez por base de datos. Si se vuelve a ejecutar no daña nada: solo toca las
actividades que todavía tienen una categoría anterior.

La conexión es la misma de la aplicación: MONGO_URI y MONGO_DB_NAME del entorno o del .env.

Uso, desde la raíz del proyecto:
    python herramientas/migrar_categorias.py             (solo muestra lo que haría)
    python herramientas/migrar_categorias.py --aplicar   (hace los cambios)
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

load_dotenv()

from app.config import Config  # noqa: E402  (debe leerse después de cargar el .env)
from app.models.enums import Categoria  # noqa: E402

EQUIVALENCIAS = {
    "PRODUCCION": Categoria.OPERACION.value,
    "MANTENIMIENTO": Categoria.OPERACION.value,
    "LIMPIEZA": Categoria.OPERACION.value,
    "CALIDAD": Categoria.REVISION.value,
    "LOGISTICA": Categoria.TRASLADO.value,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Migración de las categorías de actividad de GestLab.")
    parser.add_argument("--aplicar", action="store_true", help="Hace los cambios. Sin esta opción solo los muestra.")
    argumentos = parser.parse_args()

    cliente = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
    db = cliente[Config.MONGO_DB_NAME]
    print(f"Base de datos: {Config.MONGO_DB_NAME}")
    try:
        for anterior, nueva in EQUIVALENCIAS.items():
            filtro = {"categoria": anterior}
            cantidad = db["actividades"].count_documents(filtro)
            if not cantidad:
                continue
            if argumentos.aplicar:
                db["actividades"].update_many(filtro, {"$set": {"categoria": nueva}})
                print(f"{anterior} -> {nueva}: {cantidad} actividades cambiadas")
            else:
                print(f"{anterior} -> {nueva}: {cantidad} actividades por cambiar")
    except PyMongoError as error:
        print(f"No se pudo hablar con la base de datos: {error}")
        return 1
    if not argumentos.aplicar:
        print("No se cambió nada. Para aplicar: python herramientas/migrar_categorias.py --aplicar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
