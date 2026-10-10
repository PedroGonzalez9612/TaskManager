from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from app.models.enums import EstadoAsignacion
from app.repositories.base_repository import BaseRepository

ACTIVA = EstadoAsignacion.ACTIVA.value


class AsignacionRepository(BaseRepository):
    """Una asignación une una actividad con un operario. Una actividad puede tener varias.

    Las asignaciones no se borran: se cierran (DEVUELTA o RETIRADA) y quedan como historial. Por eso
    las búsquedas devuelven solo las activas, salvo que se pida el historial."""

    def __init__(self, db):
        super().__init__(db["asignaciones"])

    def crear_indices(self) -> None:
        # Una persona no puede tener dos asignaciones activas a la misma actividad. Las cerradas no
        # entran al índice, así que se le puede volver a asignar después de una devolución.
        self.collection.create_index(
            [("actividad_id", ASCENDING), ("usuario_id", ASCENDING)],
            name="asignacion_activa_unica",
            unique=True,
            partialFilterExpression={"estado": ACTIVA},
        )
        # Para "las actividades de este operario" (pantalla del Operario y cálculo de la carga).
        self.collection.create_index(
            [("usuario_id", ASCENDING), ("estado", ASCENDING)],
            name="usuario_estado",
        )

    @staticmethod
    def _con_estado(filtro: dict, incluir_historial: bool) -> dict:
        """Deja solo las activas. Los documentos anteriores a esta regla no tienen el campo
        "estado" y cuentan como activos (en MongoDB, comparar con None incluye el campo ausente)."""
        if not incluir_historial:
            filtro["estado"] = {"$in": [ACTIVA, None]}
        return filtro

    def find_by_actividad(self, actividad_id: str, incluir_historial: bool = False):
        filtro = self._con_estado({"actividad_id": actividad_id}, incluir_historial)
        return list(self.collection.find(filtro))

    def find_by_actividades(self, actividad_ids: list, incluir_historial: bool = False):
        filtro = self._con_estado({"actividad_id": {"$in": actividad_ids}}, incluir_historial)
        return list(self.collection.find(filtro))

    def find_by_usuario(self, usuario_id: str, incluir_historial: bool = False):
        filtro = self._con_estado({"usuario_id": usuario_id}, incluir_historial)
        return list(self.collection.find(filtro))

    def find_by_usuarios(self, usuario_ids: list, incluir_historial: bool = False):
        filtro = self._con_estado({"usuario_id": {"$in": usuario_ids}}, incluir_historial)
        return list(self.collection.find(filtro))

    def find_activa(self, actividad_id: str, usuario_id: str):
        """La asignación activa de ese operario a esa actividad, o None."""
        filtro = self._con_estado({"actividad_id": actividad_id, "usuario_id": usuario_id}, False)
        return self.collection.find_one(filtro)

    def existe(self, actividad_id: str, usuario_id: str, incluir_historial: bool = False) -> bool:
        filtro = self._con_estado({"actividad_id": actividad_id, "usuario_id": usuario_id}, incluir_historial)
        return self.collection.count_documents(filtro, limit=1) > 0

    def contar_activas(self, actividad_id: str) -> int:
        """Cuántos operarios tienen asignada la actividad en este momento."""
        return self.collection.count_documents(self._con_estado({"actividad_id": actividad_id}, False))

    def insertar_activa(self, documento: dict):
        """Inserta una asignación (Asignacion.to_dict()). Devuelve su id, o None si la base de datos
        la rechazó porque ese operario ya tiene una asignación activa a esa actividad (dos
        administradores asignando al tiempo)."""
        try:
            return self.insert(documento)
        except DuplicateKeyError:
            return None

    # Se retira cuando el servicio deje de usarlo: las asignaciones ya no se borran, se cierran.
    def delete_by_actividad(self, actividad_id: str) -> None:
        self.collection.delete_many({"actividad_id": actividad_id})

    # Se retira cuando el servicio deje de usarlo: las asignaciones ya no se borran, se cierran.
    def delete_by_actividades(self, actividad_ids: list) -> None:
        self.collection.delete_many({"actividad_id": {"$in": actividad_ids}})
