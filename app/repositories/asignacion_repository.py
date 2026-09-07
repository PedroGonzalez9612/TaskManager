from app.repositories.base_repository import BaseRepository


class AsignacionRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db["asignaciones"])

    def find_by_actividad(self, actividad_id: str):
        return self.collection.find_one({"actividad_id": actividad_id})

    def find_by_usuario(self, usuario_id: str):
        return list(self.collection.find({"usuario_id": usuario_id}))
