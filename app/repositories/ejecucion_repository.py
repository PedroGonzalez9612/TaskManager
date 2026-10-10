from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from app.models.enums import EstadoEjecucion
from app.repositories.base_repository import BaseRepository

EN_PROGRESO = EstadoEjecucion.EN_PROGRESO.value
ESTADOS_ABIERTOS = [EstadoEjecucion.EN_PROGRESO.value, EstadoEjecucion.PAUSADA.value]


class EjecucionRepository(BaseRepository):
    """Hay una ejecución por asignación (un operario en una actividad), así que una actividad con
    varios operarios tiene varias. Las pausas van dentro del documento, en la lista "pausas"."""

    def __init__(self, db):
        super().__init__(db["ejecuciones"])

    def crear_indices(self) -> None:
        # Una sola ejecución por asignación. Parcial: los documentos anteriores no tienen el campo.
        self.collection.create_index(
            [("asignacion_id", ASCENDING)],
            name="asignacion_unica",
            unique=True,
            partialFilterExpression={"asignacion_id": {"$type": "string"}},
        )
        # Regla "un operario tiene una sola actividad en ejecución a la vez" (alcance, Sección 5.1).
        # El servicio la comprueba antes de iniciar, pero dos peticiones simultáneas pasarían ambas
        # esa comprobación. Con este índice es la base de datos la que rechaza la segunda, tanto al
        # insertar como al reanudar (cambiar el estado a EN_PROGRESO).
        self.collection.create_index(
            [("usuario_id", ASCENDING)],
            name="una_en_progreso_por_usuario",
            unique=True,
            partialFilterExpression={"estado": EN_PROGRESO, "usuario_id": {"$type": "string"}},
        )
        # Para traer las ejecuciones de varias actividades (listados y análisis).
        self.collection.create_index([("actividad_id", ASCENDING)], name="actividad")

    # ---------- Consultas ----------

    def find_by_asignacion(self, asignacion_id: str):
        return self.collection.find_one({"asignacion_id": asignacion_id})

    def find_en_progreso_de_usuario(self, usuario_id: str):
        """La ejecución que el operario tiene en curso, o None. Solo puede haber una."""
        return self.collection.find_one({"usuario_id": usuario_id, "estado": EN_PROGRESO})

    def find_abiertas_de_usuario(self, usuario_id: str):
        """Las que el operario tiene en curso o pausadas."""
        return list(self.collection.find({"usuario_id": usuario_id, "estado": {"$in": ESTADOS_ABIERTOS}}))

    def find_abiertas_de_actividad(self, actividad_id: str):
        """Las ejecuciones en curso o pausadas de una actividad, de cualquiera de sus operarios."""
        return list(self.collection.find({"actividad_id": actividad_id, "estado": {"$in": ESTADOS_ABIERTOS}}))

    def find_by_actividades(self, actividad_ids: list):
        """Todas las ejecuciones de esas actividades. Puede haber varias por actividad."""
        return list(self.collection.find({"actividad_id": {"$in": actividad_ids}}))

    # ---------- Escritura ----------

    def insertar_en_progreso(self, documento: dict):
        """Inserta una ejecución que nace EN_PROGRESO. Devuelve su id, o None si la base de datos
        la rechazó porque el operario ya tiene otra en curso o porque esa asignación ya tiene
        ejecución (dos peticiones al tiempo)."""
        try:
            return self.insert(documento)
        except DuplicateKeyError:
            return None

    def guardar(self, ejecucion_id: str, documento: dict, estado_esperado: str = None) -> bool:
        """Guarda los campos de Ejecucion.to_dict(). Con estado_esperado, solo si la ejecución sigue
        en ese estado. Devuelve False si no se guardó: el estado ya era otro, el id no existe, o el
        cambio dejaría al operario con dos ejecuciones en curso (al reanudar)."""
        condicion = {"estado": estado_esperado} if estado_esperado else {}
        try:
            return self.actualizar_si(ejecucion_id, condicion, documento)
        except DuplicateKeyError:
            return False

    # ---------- Se retiran cuando los servicios dejen de usarlos ----------

    # Se retira cuando el servicio deje de usarlo: ya no hay una sola ejecución por actividad.
    def find_by_actividad(self, actividad_id: str):
        return self.collection.find_one({"actividad_id": actividad_id})

    # Se retira cuando el servicio deje de usarlo: las ejecuciones ya no se borran.
    def delete_by_actividades(self, actividad_ids: list) -> None:
        self.collection.delete_many({"actividad_id": {"$in": actividad_ids}})
