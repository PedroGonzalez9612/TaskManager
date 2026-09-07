from app.repositories.base_repository import BaseRepository


class RegistroTiempoRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db["registros_tiempo"])

    def find_by_actividad(self, actividad_id: str):
        return list(self.collection.find({"actividad_id": actividad_id}))

    def find_by_usuario(self, usuario_id: str):
        return list(self.collection.find({"usuario_id": usuario_id}))

    def total_horas_por_actividad(self):
        pipeline = [
            {"$group": {"_id": "$actividad_id", "total_horas": {"$sum": "$horas"}}},
        ]
        return list(self.collection.aggregate(pipeline))

    def total_horas_por_usuario(self):
        pipeline = [
            {"$group": {"_id": "$usuario_id", "total_horas": {"$sum": "$horas"}}},
        ]
        return list(self.collection.aggregate(pipeline))

    def total_horas_por_actividades(self, actividad_ids: list):
        pipeline = [
            {"$match": {"actividad_id": {"$in": actividad_ids}}},
            {"$group": {"_id": None, "total_horas": {"$sum": "$horas"}}},
        ]
        result = list(self.collection.aggregate(pipeline))
        return result[0]["total_horas"] if result else 0
