from bson import ObjectId
from bson.errors import InvalidId


class BaseRepository:
    def __init__(self, collection):
        self.collection = collection

    @staticmethod
    def to_object_id(id_str):
        try:
            return ObjectId(id_str)
        except (InvalidId, TypeError):
            return None

    def insert(self, document: dict) -> str:
        result = self.collection.insert_one(document)
        return str(result.inserted_id)

    def find_by_id(self, id_str: str):
        oid = self.to_object_id(id_str)
        if oid is None:
            return None
        return self.collection.find_one({"_id": oid})

    def find_all(self, filter_query: dict = None):
        return list(self.collection.find(filter_query or {}))

    def update(self, id_str: str, updates: dict) -> bool:
        oid = self.to_object_id(id_str)
        if oid is None:
            return False
        result = self.collection.update_one({"_id": oid}, {"$set": updates})
        return result.matched_count > 0

    def actualizar_si(self, id_str: str, condicion: dict, cambios: dict) -> bool:
        """Aplica los cambios solo si el documento, además de tener ese id, cumple la condición
        (por ejemplo {"estado": "EN_PROGRESO"}). Devuelve si lo encontró en esa condición.

        MongoDB comprueba y escribe en un solo paso: si dos peticiones intentan la misma transición
        al tiempo, solo una recibe True."""
        oid = self.to_object_id(id_str)
        if oid is None:
            return False
        filtro = dict(condicion or {})
        filtro["_id"] = oid
        result = self.collection.update_one(filtro, {"$set": cambios})
        return result.matched_count > 0

    def delete(self, id_str: str) -> bool:
        oid = self.to_object_id(id_str)
        if oid is None:
            return False
        result = self.collection.delete_one({"_id": oid})
        return result.deleted_count > 0
