from app.repositories.base_repository import BaseRepository


class EmpresaRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db["empresas"])
