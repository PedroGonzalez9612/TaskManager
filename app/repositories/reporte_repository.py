from pymongo import ASCENDING, DESCENDING

from app.repositories.base_repository import BaseRepository


class ReporteRepository(BaseRepository):
    """Reportes de actividad de los operarios. No se borran: se convierten o se descartan."""

    def __init__(self, db):
        super().__init__(db["reportes"])

    def crear_indices(self) -> None:
        # El Administrador pide los de su empresa por revisar; el Operario, los suyos más recientes.
        self.collection.create_index([("empresa_id", ASCENDING), ("estado", ASCENDING)], name="empresa_estado")
        self.collection.create_index([("operario_id", ASCENDING), ("fecha", DESCENDING)], name="operario_fecha")

    def find_de_empresa(self, empresa_id: str, estado: str = None) -> list:
        """Los de la empresa, del más antiguo al más reciente (el que más espera va primero)."""
        filtro = {"empresa_id": empresa_id}
        if estado:
            filtro["estado"] = estado
        return list(self.collection.find(filtro).sort("fecha", ASCENDING))

    def find_de_operario(self, operario_id: str, limite: int) -> list:
        """Los últimos que reportó ese operario, del más reciente al más antiguo."""
        return list(self.collection.find({"operario_id": operario_id}).sort("fecha", DESCENDING).limit(limite))
