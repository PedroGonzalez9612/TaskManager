from pymongo import ASCENDING

from app.repositories.base_repository import BaseRepository


class OrdenJornadaRepository(BaseRepository):
    """El orden que cada operario eligió para sus actividades de un día (alcance, Sección 5.1).
    Hay un solo documento por operario y jornada."""

    def __init__(self, db):
        super().__init__(db["ordenes_jornada"])

    def crear_indices(self) -> None:
        # Único: dos peticiones a la vez no pueden dejar dos órdenes para el mismo operario y día.
        self.collection.create_index(
            [("usuario_id", ASCENDING), ("fecha", ASCENDING)], unique=True, name="orden_unico_por_dia")

    def find_de_usuario(self, usuario_id: str, fecha: str):
        return self.collection.find_one({"usuario_id": usuario_id, "fecha": fecha})

    def guardar(self, documento: dict) -> None:
        """Crea o reemplaza el orden de ese operario para esa jornada, en una sola operación."""
        filtro = {"usuario_id": documento["usuario_id"], "fecha": documento["fecha"]}
        self.collection.update_one(filtro, {"$set": documento}, upsert=True)

    def eliminar(self, usuario_id: str, fecha: str) -> None:
        self.collection.delete_one({"usuario_id": usuario_id, "fecha": fecha})
