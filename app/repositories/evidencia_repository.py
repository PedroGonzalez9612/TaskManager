from pymongo import ASCENDING

from app.repositories.base_repository import BaseRepository

# Las consultas de listado no traen los bytes del archivo: solo sus datos.
SIN_CONTENIDO = {"contenido": 0}


class EvidenciaRepository(BaseRepository):
    """Fotos y adjuntos de las ejecuciones. El archivo se guarda dentro del documento, como el logo
    de la empresa: con el límite de 5 MB por archivo cabe sin pasar del máximo de MongoDB (16 MB)."""

    def __init__(self, db):
        super().__init__(db["evidencias"])

    def crear_indices(self) -> None:
        # Las evidencias se piden siempre por ejecución: las de una o las de varias a la vez.
        self.collection.create_index([("ejecucion_id", ASCENDING)], name="ejecucion")

    def insertar(self, datos: dict, contenido: bytes) -> str:
        return self.insert({**datos, "contenido": contenido})

    def contar_de_ejecucion(self, ejecucion_id: str) -> int:
        return self.collection.count_documents({"ejecucion_id": ejecucion_id})

    def find_de_ejecuciones(self, ejecucion_ids) -> list:
        """Las evidencias de esas ejecuciones, sin el archivo, en el orden en que se subieron."""
        if not ejecucion_ids:
            return []
        return list(self.collection.find({"ejecucion_id": {"$in": list(ejecucion_ids)}}, SIN_CONTENIDO)
                    .sort("fecha", ASCENDING))

    def find_datos(self, evidencia_id: str):
        """Los datos de una evidencia, sin el archivo (para comprobar quién la puede ver)."""
        oid = self.to_object_id(evidencia_id)
        return self.collection.find_one({"_id": oid}, SIN_CONTENIDO) if oid else None

    def find_contenido(self, evidencia_id: str):
        """Los bytes del archivo, o None."""
        oid = self.to_object_id(evidencia_id)
        doc = self.collection.find_one({"_id": oid}, {"contenido": 1}) if oid else None
        return bytes(doc["contenido"]) if doc else None
