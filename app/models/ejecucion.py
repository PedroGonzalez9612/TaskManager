from app.models.enums import EstadoEjecucion


class Ejecucion:
    def __init__(self, actividad_id, estado=EstadoEjecucion.NO_INICIADA,
                 fecha_inicio=None, fecha_fin=None, id=None):
        self.id = id
        self.actividad_id = actividad_id
        self.estado = estado
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin

    def to_dict(self):
        return {
            "actividad_id": self.actividad_id,
            "estado": self.estado.value if isinstance(self.estado, EstadoEjecucion) else self.estado,
            "fecha_inicio": self.fecha_inicio,
            "fecha_fin": self.fecha_fin,
        }

    @staticmethod
    def from_doc(doc):
        return {
            "id": str(doc["_id"]),
            "actividad_id": doc["actividad_id"],
            "estado": doc.get("estado", EstadoEjecucion.NO_INICIADA.value),
            "fecha_inicio": doc.get("fecha_inicio"),
            "fecha_fin": doc.get("fecha_fin"),
        }
