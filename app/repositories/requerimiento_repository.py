from app.repositories.base_repository import BaseRepository


class RequerimientoRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db["requerimientos"])

    def find_by_empresa(self, empresa_id: str):
        return list(self.collection.find({"empresa_id": empresa_id}))
