from datetime import datetime, timezone


class Asignacion:
    def __init__(self, actividad_id, usuario_id, fecha_asignacion=None, id=None):
        self.id = id
        self.actividad_id = actividad_id
        self.usuario_id = usuario_id
        self.fecha_asignacion = fecha_asignacion or datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "actividad_id": self.actividad_id,
            "usuario_id": self.usuario_id,
            "fecha_asignacion": self.fecha_asignacion,
        }

    @staticmethod
    def from_doc(doc):
        return {
            "id": str(doc["_id"]),
            "actividad_id": doc["actividad_id"],
            "usuario_id": doc["usuario_id"],
            "fecha_asignacion": doc.get("fecha_asignacion"),
        }
