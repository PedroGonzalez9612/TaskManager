"""Migración de la Etapa 4: asignaciones que no se borran y ejecución por asignación.

Se ejecuta a mano, una sola vez, contra la base de datos de desarrollo. Si se vuelve a
ejecutar no daña nada: cada paso solo toca lo que todavía está en la forma anterior.

Qué hace:
1. Pone estado "ACTIVA" a las asignaciones que no tienen estado (las anteriores a la regla).
2. Vacía la colección "ejecuciones": son datos de prueba y no dicen qué operario las hizo.
3. Devuelve a "ASIGNADA" las actividades que estaban "EN_EJECUCION", porque su ejecución ya
   no existe. Las "COMPLETADA" se dejan como están.
4. Crea los índices nuevos de actividades, asignaciones y ejecuciones.

La conexión es la misma de la aplicación: MONGO_URI y MONGO_DB_NAME del entorno o del .env.

Uso, desde la raíz del proyecto:
    python herramientas/migrar_etapa4.py             (solo muestra lo que haría)
    python herramientas/migrar_etapa4.py --aplicar   (hace los cambios)
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import OperationFailure, PyMongoError

# Permite importar "app" al ejecutar el script directamente desde la raíz del proyecto.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

load_dotenv()

from app.config import Config  # noqa: E402  (debe leerse después de cargar el .env)
from app.models.enums import EstadoActividad, EstadoAsignacion  # noqa: E402
from app.repositories import crear_indices  # noqa: E402

SIN_ESTADO = {"estado": {"$exists": False}}
EN_EJECUCION = {"estado": EstadoActividad.EN_EJECUCION.value}


def asignaciones_activas_repetidas(db) -> list:
    """Pares (actividad, operario) con más de una asignación activa. Impedirían crear el índice único."""
    activas = {"estado": {"$in": [EstadoAsignacion.ACTIVA.value, None]}}
    return list(db["asignaciones"].aggregate([
        {"$match": activas},
        {"$group": {"_id": {"actividad_id": "$actividad_id", "usuario_id": "$usuario_id"}, "cantidad": {"$sum": 1}}},
        {"$match": {"cantidad": {"$gt": 1}}},
    ]))


def mostrar_plan(db) -> None:
    print(f"- Asignaciones sin estado que pasarían a ACTIVA: {db['asignaciones'].count_documents(SIN_ESTADO)}")
    print(f"- Ejecuciones que se borrarían: {db['ejecuciones'].count_documents({})}")
    print(f"- Actividades EN_EJECUCION que volverían a ASIGNADA: {db['actividades'].count_documents(EN_EJECUCION)}")
    print("- Índices que se crearían si no existen:")
    print("    actividades:  (empresa_id, fecha_programada)")
    print("    asignaciones: (actividad_id, usuario_id) único, solo entre las ACTIVA")
    print("    asignaciones: (usuario_id, estado)")
    print("    ejecuciones:  (asignacion_id) único, solo donde es texto")
    print("    ejecuciones:  (usuario_id) único, solo entre las EN_PROGRESO")
    print("    ejecuciones:  (actividad_id)")


def aplicar(db) -> bool:
    resultado = db["asignaciones"].update_many(SIN_ESTADO, {"$set": {"estado": EstadoAsignacion.ACTIVA.value}})
    print(f"- Asignaciones que pasaron a ACTIVA: {resultado.modified_count}")

    resultado = db["ejecuciones"].delete_many({})
    print(f"- Ejecuciones borradas: {resultado.deleted_count}")

    resultado = db["actividades"].update_many(EN_EJECUCION, {"$set": {"estado": EstadoActividad.ASIGNADA.value}})
    print(f"- Actividades que volvieron de EN_EJECUCION a ASIGNADA: {resultado.modified_count}")

    try:
        crear_indices(db)
    except OperationFailure as error:
        print(f"ERROR: no se pudieron crear todos los índices: {error}")
        return False
    print("- Índices creados o ya existentes:")
    for coleccion in ("actividades", "asignaciones", "ejecuciones"):
        nombres = sorted(nombre for nombre in db[coleccion].index_information() if nombre != "_id_")
        print(f"    {coleccion}: {', '.join(nombres)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Migración de datos de la Etapa 4 de GestLab.")
    parser.add_argument("--aplicar", action="store_true", help="Hace los cambios. Sin esta opción solo los muestra.")
    args = parser.parse_args()

    cliente = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
    db = cliente[Config.MONGO_DB_NAME]
    # No se imprime la URI: puede traer usuario y contraseña.
    print(f"Base de datos: {Config.MONGO_DB_NAME}")

    try:
        repetidas = asignaciones_activas_repetidas(db)
        for grupo in repetidas:
            print(f"AVISO: {grupo['cantidad']} asignaciones activas repetidas: actividad "
                  f"{grupo['_id'].get('actividad_id')}, operario {grupo['_id'].get('usuario_id')}")
        if repetidas:
            print("AVISO: con asignaciones repetidas no se puede crear el índice único. Deja una sola "
                  "por actividad y operario, y vuelve a ejecutar el script.")

        if not args.aplicar:
            print("Modo de solo consulta. Esto es lo que haría con --aplicar:")
            mostrar_plan(db)
            return 0

        print("Aplicando la migración:")
        completa = aplicar(db)
    except PyMongoError as error:
        print(f"ERROR: no se pudo trabajar con MongoDB: {error}")
        return 1
    finally:
        cliente.close()

    print("Migración terminada." if completa else "Migración incompleta: revisa el error de los índices.")
    return 0 if completa else 1


if __name__ == "__main__":
    sys.exit(main())
