from app.repositories.base_repository import BaseRepository

# El logo puede pesar cientos de KB: las consultas normales no lo traen.
SIN_LOGO = {"logo": 0}


class EmpresaRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db["empresas"])

    def find_by_id(self, id_str: str):
        oid = self.to_object_id(id_str)
        if oid is None:
            return None
        return self.collection.find_one({"_id": oid}, SIN_LOGO)

    def find_all(self, filter_query: dict = None):
        return list(self.collection.find(filter_query or {}, SIN_LOGO))

    def find_by_nit(self, nit: str):
        return self.collection.find_one({"nit": nit}, SIN_LOGO)

    def find_logo(self, id_str: str):
        oid = self.to_object_id(id_str)
        if oid is None:
            return None
        return self.collection.find_one({"_id": oid}, {"logo": 1, "logo_tipo": 1})
