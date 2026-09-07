from app.repositories.base_repository import BaseRepository


class ActividadRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db["actividades"])

    def find_by_requerimiento(self, requerimiento_id: str):
        return list(self.collection.find({"requerimiento_id": requerimiento_id}))

    def contar_por_estado(self, requerimiento_id: str = None):
        match_stage = {"$match": {"requerimiento_id": requerimiento_id}} if requerimiento_id else None
        pipeline = ([match_stage] if match_stage else []) + [
            {"$group": {"_id": "$estado", "total": {"$sum": 1}}},
        ]
        return list(self.collection.aggregate(pipeline))
