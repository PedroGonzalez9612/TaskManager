from datetime import datetime, timezone

from app.models.enums import EstadoRequerimiento


class Requerimiento:
    def __init__(self, titulo, descripcion, empresa_id, estado=EstadoRequerimiento.ABIERTO,
                 fecha_creacion=None, id=None):
        self.id = id
        self.titulo = titulo
        self.descripcion = descripcion
        self.empresa_id = empresa_id
        self.estado = estado
        self.fecha_creacion = fecha_creacion or datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "empresa_id": self.empresa_id,
            "estado": self.estado.value if isinstance(self.estado, EstadoRequerimiento) else self.estado,
            "fecha_creacion": self.fecha_creacion,
        }

    @staticmethod
    def from_doc(doc):
        return {
            "id": str(doc["_id"]),
            "titulo": doc["titulo"],
            "descripcion": doc.get("descripcion", ""),
            "empresa_id": doc["empresa_id"],
            "estado": doc.get("estado", EstadoRequerimiento.ABIERTO.value),
            "fecha_creacion": doc.get("fecha_creacion"),
        }
