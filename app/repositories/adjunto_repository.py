from pymongo import ASCENDING

from app.repositories.base_repository import BaseRepository

# Las consultas de listado no traen los bytes del archivo: solo sus datos.
SIN_CONTENIDO = {"contenido": 0}


class AdjuntoRepository(BaseRepository):
    """Adjuntos de la información de las actividades. Como la evidencia, el archivo va dentro del
    documento: con 5 MB por archivo no se pasa del máximo de MongoDB (16 MB)."""

    def __init__(self, db):
        super().__init__(db["adjuntos"])

    def crear_indices(self) -> None:
        # Los adjuntos se piden siempre por actividad: los de una o los de varias a la vez.
        self.collection.create_index([("actividad_id", ASCENDING)], name="actividad")

    def insertar(self, datos: dict, contenido: bytes) -> str:
        return self.insert({**datos, "contenido": contenido})

    def contar_de_actividad(self, actividad_id: str) -> int:
        return self.collection.count_documents({"actividad_id": actividad_id})

    def find_de_actividades(self, actividad_ids) -> list:
        """Los adjuntos de esas actividades, sin el archivo, en el orden en que se subieron."""
        if not actividad_ids:
            return []
        return list(self.collection.find({"actividad_id": {"$in": list(actividad_ids)}}, SIN_CONTENIDO)
                    .sort("fecha", ASCENDING))

    def find_datos(self, adjunto_id: str):
        oid = self.to_object_id(adjunto_id)
        return self.collection.find_one({"_id": oid}, SIN_CONTENIDO) if oid else None

    def find_contenido(self, adjunto_id: str):
        oid = self.to_object_id(adjunto_id)
        doc = self.collection.find_one({"_id": oid}, {"contenido": 1}) if oid else None
        return bytes(doc["contenido"]) if doc else None
