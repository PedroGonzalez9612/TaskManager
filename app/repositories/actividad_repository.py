from app.repositories.base_repository import BaseRepository


class ActividadRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db["actividades"])

    def find_by_requerimiento(self, requerimiento_id: str):
        return list(self.collection.find({"requerimiento_id": requerimiento_id}))

    def buscar(self, empresa_id: str, requerimiento_id: str = None, fecha_desde: str = None,
               fecha_hasta: str = None, ids: list = None):
        """Actividades de una empresa, con filtros opcionales. Las fechas son textos "AAAA-MM-DD"."""
        filtro = {"empresa_id": empresa_id}
        if requerimiento_id:
            filtro["requerimiento_id"] = requerimiento_id
        if fecha_desde or fecha_hasta:
            rango = {}
            if fecha_desde:
                rango["$gte"] = fecha_desde
            if fecha_hasta:
                rango["$lte"] = fecha_hasta
            filtro["fecha_programada"] = rango
        if ids is not None:
            filtro["_id"] = {"$in": [oid for oid in map(self.to_object_id, ids) if oid]}
        return list(self.collection.find(filtro).sort([("fecha_programada", 1), ("hora_programada", 1)]))

    def contar_por_requerimiento(self, empresa_id: str) -> dict:
        grupos = self.collection.aggregate([
            {"$match": {"empresa_id": empresa_id}},
            {"$group": {"_id": "$requerimiento_id", "cantidad": {"$sum": 1}}},
        ])
        return {grupo["_id"]: grupo["cantidad"] for grupo in grupos}

    def delete_by_requerimiento(self, requerimiento_id: str) -> None:
        self.collection.delete_many({"requerimiento_id": requerimiento_id})

    def contar_por_estado(self, requerimiento_id: str = None):
        match_stage = {"$match": {"requerimiento_id": requerimiento_id}} if requerimiento_id else None
        pipeline = ([match_stage] if match_stage else []) + [
            {"$group": {"_id": "$estado", "total": {"$sum": 1}}},
        ]
        return list(self.collection.aggregate(pipeline))
