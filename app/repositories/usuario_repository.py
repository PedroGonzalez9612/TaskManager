from app.repositories.base_repository import BaseRepository

# Quien trabaja hoy: los usuarios anteriores a la regla de desactivar no tienen el campo y están activos.
ACTIVOS = {"activo": {"$ne": False}}


class UsuarioRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db["usuarios"])

    def find_by_empresa(self, empresa_id: str):
        return list(self.collection.find({"empresa_id": empresa_id}))

    def find_by_empresa_y_rol(self, empresa_id: str, rol: str):
        """Los usuarios activos de ese rol: a un desactivado no se le asigna trabajo ni se le espera."""
        return list(self.collection.find({"empresa_id": empresa_id, "rol": rol, **ACTIVOS}).sort("nombre", 1))

    def find_by_ids(self, ids: list):
        oids = [oid for oid in map(self.to_object_id, ids) if oid]
        return list(self.collection.find({"_id": {"$in": oids}}))

    def find_by_correo(self, correo: str):
        return self.collection.find_one({"correo": correo})

    def contar_por_rol(self, empresa_id: str) -> dict:
        """Usuarios activos de la empresa por rol, por ejemplo {"OPERARIO": 3, "ADMINISTRADOR": 1}.
        Un desactivado no ocupa cupo en el límite."""
        grupos = self.collection.aggregate([
            {"$match": {"empresa_id": empresa_id, **ACTIVOS}},
            {"$group": {"_id": "$rol", "cantidad": {"$sum": 1}}},
        ])
        return {grupo["_id"]: grupo["cantidad"] for grupo in grupos}

    def existe_rol(self, rol: str) -> bool:
        return self.collection.count_documents({"rol": rol}, limit=1) > 0
