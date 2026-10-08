from app.repositories.base_repository import BaseRepository


class UsuarioRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db["usuarios"])

    def find_by_empresa(self, empresa_id: str):
        return list(self.collection.find({"empresa_id": empresa_id}))

    def find_by_empresa_y_rol(self, empresa_id: str, rol: str):
        return list(self.collection.find({"empresa_id": empresa_id, "rol": rol}).sort("nombre", 1))

    def find_by_ids(self, ids: list):
        oids = [oid for oid in map(self.to_object_id, ids) if oid]
        return list(self.collection.find({"_id": {"$in": oids}}))

    def find_by_correo(self, correo: str):
        return self.collection.find_one({"correo": correo})

    def contar_por_rol(self, empresa_id: str) -> dict:
        """Cantidad de usuarios de la empresa por rol, por ejemplo {"OPERARIO": 3, "ADMINISTRADOR": 1}."""
        grupos = self.collection.aggregate([
            {"$match": {"empresa_id": empresa_id}},
            {"$group": {"_id": "$rol", "cantidad": {"$sum": 1}}},
        ])
        return {grupo["_id"]: grupo["cantidad"] for grupo in grupos}

    def existe_rol(self, rol: str) -> bool:
        return self.collection.count_documents({"rol": rol}, limit=1) > 0
