from app.models.enums import EstadoActividad, Prioridad


class Actividad:
    def __init__(self, titulo, descripcion, requerimiento_id,
                 prioridad=Prioridad.MEDIA, estado=EstadoActividad.PENDIENTE, id=None):
        self.id = id
        self.titulo = titulo
        self.descripcion = descripcion
        self.requerimiento_id = requerimiento_id
        self.prioridad = prioridad
        self.estado = estado

    def to_dict(self):
        return {
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "requerimiento_id": self.requerimiento_id,
            "prioridad": self.prioridad.value if isinstance(self.prioridad, Prioridad) else self.prioridad,
            "estado": self.estado.value if isinstance(self.estado, EstadoActividad) else self.estado,
        }

    @staticmethod
    def from_doc(doc):
        return {
            "id": str(doc["_id"]),
            "titulo": doc["titulo"],
            "descripcion": doc.get("descripcion", ""),
            "requerimiento_id": doc["requerimiento_id"],
            "prioridad": doc.get("prioridad", Prioridad.MEDIA.value),
            "estado": doc.get("estado", EstadoActividad.PENDIENTE.value),
        }
