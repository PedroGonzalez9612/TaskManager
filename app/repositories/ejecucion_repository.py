from app.repositories.base_repository import BaseRepository


class EjecucionRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db["ejecuciones"])

    def find_by_actividad(self, actividad_id: str):
        return self.collection.find_one({"actividad_id": actividad_id})
