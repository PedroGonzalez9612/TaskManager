from datetime import datetime, timezone


class RegistroTiempo:
    def __init__(self, actividad_id, usuario_id, horas, descripcion="", fecha=None, id=None):
        self.id = id
        self.actividad_id = actividad_id
        self.usuario_id = usuario_id
        self.horas = horas
        self.descripcion = descripcion
        self.fecha = fecha or datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "actividad_id": self.actividad_id,
            "usuario_id": self.usuario_id,
            "horas": self.horas,
            "descripcion": self.descripcion,
            "fecha": self.fecha,
        }

    @staticmethod
    def from_doc(doc):
        return {
            "id": str(doc["_id"]),
            "actividad_id": doc["actividad_id"],
            "usuario_id": doc["usuario_id"],
            "horas": doc["horas"],
            "descripcion": doc.get("descripcion", ""),
            "fecha": doc.get("fecha"),
        }
