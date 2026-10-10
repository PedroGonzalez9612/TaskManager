from pymongo import ASCENDING

from app.repositories.base_repository import BaseRepository


class TurnoRepository(BaseRepository):
    """El catálogo de turnos de cada empresa (alcance, Sección 5.1). Un turno no se borra: las
    asignaciones de turno de los operarios lo siguen apuntando."""

    def __init__(self, db):
        super().__init__(db["turnos"])

    def crear_indices(self) -> None:
        # La consulta de listado es "los turnos de esta empresa, por hora de inicio".
        self.collection.create_index(
            [("empresa_id", ASCENDING), ("hora_inicio", ASCENDING)], name="empresa_hora_inicio")

    def find_by_empresa(self, empresa_id: str):
        """Los turnos de la empresa, ordenados por hora de inicio y luego por nombre."""
        cursor = self.collection.find({"empresa_id": empresa_id})
        return list(cursor.sort([("hora_inicio", ASCENDING), ("nombre", ASCENDING)]))

    def find_by_ids(self, ids: list):
        oids = [oid for oid in map(self.to_object_id, ids) if oid]
        return list(self.collection.find({"_id": {"$in": oids}}))


class AsignacionTurnoRepository(BaseRepository):
    """El turno que tiene cada operario desde una fecha. Cambiar de turno inserta una asignación
    nueva: las anteriores no se modifican, para calcular los periodos pasados con el turno de entonces."""

    def __init__(self, db):
        super().__init__(db["asignaciones_turno"])

    def crear_indices(self) -> None:
        self.collection.create_index(
            [("usuario_id", ASCENDING), ("desde", ASCENDING)], name="usuario_desde")

    def find_de_usuario(self, usuario_id: str):
        """Todas las asignaciones de turno del operario, de la más antigua a la más reciente."""
        return self.find_de_usuarios([usuario_id])

    def find_de_usuarios(self, usuario_ids: list):
        """Las asignaciones de turno de varios operarios en una sola consulta."""
        cursor = self.collection.find({"usuario_id": {"$in": list(usuario_ids)}})
        return list(cursor.sort([("desde", ASCENDING), ("fecha_registro", ASCENDING)]))
