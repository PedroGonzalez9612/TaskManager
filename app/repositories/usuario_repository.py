from app.repositories.base_repository import BaseRepository


class UsuarioRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db["usuarios"])

    def find_by_empresa(self, empresa_id: str):
        return list(self.collection.find({"empresa_id": empresa_id}))

    def find_by_email(self, email: str):
        return self.collection.find_one({"email": email})
