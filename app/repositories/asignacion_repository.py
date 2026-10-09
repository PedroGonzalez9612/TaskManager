from app.repositories.base_repository import BaseRepository


class AsignacionRepository(BaseRepository):
    """Una asignación une una actividad con un operario. Una actividad puede tener varias."""

    def __init__(self, db):
        super().__init__(db["asignaciones"])

    def find_by_actividad(self, actividad_id: str):
        return list(self.collection.find({"actividad_id": actividad_id}))

    def find_by_actividades(self, actividad_ids: list):
        return list(self.collection.find({"actividad_id": {"$in": actividad_ids}}))

    def find_by_usuario(self, usuario_id: str):
        return list(self.collection.find({"usuario_id": usuario_id}))

    def find_by_usuarios(self, usuario_ids: list):
        return list(self.collection.find({"usuario_id": {"$in": usuario_ids}}))

    def existe(self, actividad_id: str, usuario_id: str) -> bool:
        filtro = {"actividad_id": actividad_id, "usuario_id": usuario_id}
        return self.collection.count_documents(filtro, limit=1) > 0

    def delete_by_actividad(self, actividad_id: str) -> None:
        self.collection.delete_many({"actividad_id": actividad_id})

    def delete_by_actividades(self, actividad_ids: list) -> None:
        self.collection.delete_many({"actividad_id": {"$in": actividad_ids}})
