from pymongo import ASCENDING

from app.repositories.base_repository import BaseRepository


class ProyectoRepository(BaseRepository):
    """Un proyecto es un conjunto de actividades de una empresa (alcance, Sección 5.1).

    El documento no guarda el avance ni la lista de actividades: cada actividad lleva su
    "proyecto_id", y el avance se calcula con ellas (ActividadRepository.find_by_proyectos)."""

    def __init__(self, db):
        super().__init__(db["proyectos"])

    def crear_indices(self) -> None:
        # La única consulta de listado es "los proyectos de esta empresa".
        self.collection.create_index([("empresa_id", ASCENDING)], name="empresa")

    def find_by_empresa(self, empresa_id: str):
        """Los proyectos de la empresa, ordenados por nombre."""
        return list(self.collection.find({"empresa_id": empresa_id}).sort("nombre", ASCENDING))
