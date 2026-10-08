from app.repositories.base_repository import BaseRepository


class EjecucionRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db["ejecuciones"])

    def find_by_actividad(self, actividad_id: str):
        return self.collection.find_one({"actividad_id": actividad_id})

    def find_by_actividades(self, actividad_ids: list):
        return list(self.collection.find({"actividad_id": {"$in": actividad_ids}}))

    def delete_by_actividades(self, actividad_ids: list) -> None:
        self.collection.delete_many({"actividad_id": {"$in": actividad_ids}})
