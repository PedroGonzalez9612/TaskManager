from app.models.enums import Categoria, EstadoActividad, Prioridad


class Actividad:
    def __init__(self, codigo, titulo, descripcion, requerimiento_id, empresa_id, categoria, ubicacion,
                 tiempo_estimado_min, fecha_programada, hora_programada=None,
                 prioridad=Prioridad.MEDIA, estado=EstadoActividad.PENDIENTE, id=None):
        self.id = id
        self.codigo = codigo                    # Consecutivo por empresa, por ejemplo "OT-0042".
        self.titulo = titulo
        self.descripcion = descripcion
        self.requerimiento_id = requerimiento_id
        self.empresa_id = empresa_id
        self.categoria = categoria
        self.ubicacion = ubicacion
        # El tiempo estimado es de la actividad completa: no se divide entre los operarios asignados.
        self.tiempo_estimado_min = tiempo_estimado_min
        self.fecha_programada = fecha_programada    # "AAAA-MM-DD": la jornada a la que pertenece.
        self.hora_programada = hora_programada      # "HH:MM" o None si no tiene hora fija.
        self.prioridad = prioridad
        self.estado = estado

    def to_dict(self):
        return {
            "codigo": self.codigo,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "requerimiento_id": self.requerimiento_id,
            "empresa_id": self.empresa_id,
            "categoria": self.categoria.value if isinstance(self.categoria, Categoria) else self.categoria,
            "ubicacion": self.ubicacion,
            "tiempo_estimado_min": self.tiempo_estimado_min,
            "fecha_programada": self.fecha_programada,
            "hora_programada": self.hora_programada,
            "prioridad": self.prioridad.value if isinstance(self.prioridad, Prioridad) else self.prioridad,
            "estado": self.estado.value if isinstance(self.estado, EstadoActividad) else self.estado,
        }

    @staticmethod
    def from_doc(doc):
        prioridad = doc.get("prioridad", Prioridad.MEDIA.value)
        return {
            "id": str(doc["_id"]),
            "codigo": doc.get("codigo", ""),
            "titulo": doc["titulo"],
            "descripcion": doc.get("descripcion", ""),
            "requerimiento_id": doc["requerimiento_id"],
            "empresa_id": doc.get("empresa_id"),
            "categoria": doc.get("categoria"),
            "ubicacion": doc.get("ubicacion", ""),
            "tiempo_estimado_min": doc.get("tiempo_estimado_min"),
            "fecha_programada": doc.get("fecha_programada"),
            "hora_programada": doc.get("hora_programada"),
            "prioridad": prioridad,
            "peso_prioridad": Prioridad(prioridad).peso,
            "estado": doc.get("estado", EstadoActividad.PENDIENTE.value),
        }
