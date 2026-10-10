from app.models.enums import Categoria, EstadoActividad, Prioridad
from app.models.registros import Reprogramacion, Cancelacion
from app.utils.errors import ValidationError


class Actividad:
    """Unidad de trabajo. Es independiente o pertenece a un solo proyecto (alcance, Sección 5.1).

    Tiene una sola fecha programada, aunque la hagan varios operarios. Lo que le pasa (se reprogramó,
    se canceló) queda guardado dentro de ella y nunca se borra. La clase no lee el reloj: la hora
    de cada evento la pone el servidor y llega como parámetro ("ahora")."""

    def __init__(self, codigo, titulo, descripcion, empresa_id, categoria, ubicacion,
                 tiempo_estimado_min, fecha_programada, hora_programada=None,
                 prioridad=Prioridad.MEDIA, estado=EstadoActividad.PENDIENTE,
                 proyecto_id=None, requerimiento_id=None):
        # Una actividad nueva no tiene id ni historial: eso lo pone desde_documento al leerla.
        self.id = None
        self.codigo = codigo                    # Consecutivo por empresa, por ejemplo "OT-0042".
        self.titulo = titulo
        self.descripcion = descripcion
        self.proyecto_id = proyecto_id          # None: es una actividad independiente.
        self.requerimiento_id = requerimiento_id    # Dato anterior a los proyectos; se retira con ellos.
        self.empresa_id = empresa_id
        self.categoria = categoria
        self.ubicacion = ubicacion
        # El tiempo estimado es de la actividad completa: no se divide entre los operarios asignados.
        self.tiempo_estimado_min = tiempo_estimado_min
        self.fecha_programada = fecha_programada    # "AAAA-MM-DD": la jornada a la que pertenece.
        self.hora_programada = hora_programada      # "HH:MM" si es de hora fija; None si es de horario flexible.
        self.fecha_original = fecha_programada      # La jornada para la que se programó.
        self.prioridad = prioridad
        self.estado = EstadoActividad(estado)
        self.reprogramaciones = []
        self.cancelacion = None
        self.fecha_no_realizada = None

    # ---------- Consultas ----------

    @property
    def es_hora_fija(self) -> bool:
        return bool(self.hora_programada)

    @property
    def es_final(self) -> bool:
        return self.estado.es_final

    @property
    def fue_reprogramada(self) -> bool:
        """"Actividad reprogramada" no es un estado: una reprogramada puede estar por iniciar o pausada."""
        return bool(self.reprogramaciones)

    # ---------- Transiciones ----------

    def cancelar(self, motivo, autor_id, ahora) -> None:
        """Solo el Administrador (lo comprueba el servicio). No se cancela lo que alguien tiene en curso."""
        if self.es_final:
            raise ValidationError("Esta actividad ya terminó y no se puede cancelar")
        if self.estado == EstadoActividad.EN_EJECUCION:
            raise ValidationError("Alguien tiene esta actividad en curso. Debe pausarla antes de poder cancelarla")
        self.cancelacion = Cancelacion(motivo, autor_id, ahora)
        self.estado = EstadoActividad.CANCELADA

    def reprogramar(self, jornada_destino, ahora) -> None:
        """Una actividad de horario flexible que no se terminó en su jornada pasa a otra. El estado no cambia."""
        if self.es_final:
            raise ValidationError("Una actividad terminada no se reprograma")
        if self.es_hora_fija:
            raise ValidationError("Una actividad de hora fija no se reprograma")
        if jornada_destino <= self.fecha_programada:
            raise ValidationError("La actividad solo se reprograma a una jornada posterior")
        self.reprogramaciones.append(Reprogramacion(self.fecha_programada, jornada_destino, ahora))
        self.fecha_programada = jornada_destino

    def marcar_no_realizada(self, ahora) -> None:
        """Una actividad de hora fija que no se terminó en su día. Es definitivo."""
        if self.es_final:
            raise ValidationError("Esta actividad ya terminó")
        if not self.es_hora_fija:
            raise ValidationError("Solo una actividad de hora fija queda como No realizada")
        self.estado = EstadoActividad.NO_REALIZADA
        self.fecha_no_realizada = ahora

    # ---------- Persistencia y presentación ----------

    def to_dict(self):
        return {
            "codigo": self.codigo,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "proyecto_id": self.proyecto_id,
            "requerimiento_id": self.requerimiento_id,
            "empresa_id": self.empresa_id,
            "categoria": self.categoria.value if isinstance(self.categoria, Categoria) else self.categoria,
            "ubicacion": self.ubicacion,
            "tiempo_estimado_min": self.tiempo_estimado_min,
            "fecha_programada": self.fecha_programada,
            "hora_programada": self.hora_programada,
            "fecha_original": self.fecha_original,
            "prioridad": self.prioridad.value if isinstance(self.prioridad, Prioridad) else self.prioridad,
            "estado": self.estado.value,
            "reprogramaciones": [reprogramacion.to_dict() for reprogramacion in self.reprogramaciones],
            "cancelacion": self.cancelacion.to_dict() if self.cancelacion else None,
            "fecha_no_realizada": self.fecha_no_realizada,
        }

    @classmethod
    def desde_documento(cls, doc: dict) -> "Actividad":
        actividad = cls(
            codigo=doc.get("codigo", ""),
            titulo=doc["titulo"],
            descripcion=doc.get("descripcion", ""),
            proyecto_id=doc.get("proyecto_id"),
            requerimiento_id=doc.get("requerimiento_id"),
            empresa_id=doc.get("empresa_id"),
            categoria=doc.get("categoria"),
            ubicacion=doc.get("ubicacion", ""),
            tiempo_estimado_min=doc.get("tiempo_estimado_min"),
            fecha_programada=doc.get("fecha_programada"),
            hora_programada=doc.get("hora_programada"),
            prioridad=doc.get("prioridad", Prioridad.MEDIA.value),
            estado=doc.get("estado", EstadoActividad.PENDIENTE.value),
        )
        actividad.id = str(doc["_id"])
        cancelacion = doc.get("cancelacion")
        actividad.fecha_original = doc.get("fecha_original") or actividad.fecha_programada
        actividad.reprogramaciones = [Reprogramacion.desde_documento(reprogramacion) for reprogramacion in doc.get("reprogramaciones", [])]
        actividad.cancelacion = Cancelacion.desde_documento(cancelacion) if cancelacion else None
        actividad.fecha_no_realizada = doc.get("fecha_no_realizada")
        return actividad

    @staticmethod
    def from_doc(doc):
        """La actividad como diccionario para la API."""
        prioridad = doc.get("prioridad", Prioridad.MEDIA.value)
        reprogramaciones = doc.get("reprogramaciones", [])
        return {
            "id": str(doc["_id"]),
            "codigo": doc.get("codigo", ""),
            "titulo": doc["titulo"],
            "descripcion": doc.get("descripcion", ""),
            "proyecto_id": doc.get("proyecto_id"),
            "requerimiento_id": doc.get("requerimiento_id"),
            "empresa_id": doc.get("empresa_id"),
            "categoria": doc.get("categoria"),
            "ubicacion": doc.get("ubicacion", ""),
            "tiempo_estimado_min": doc.get("tiempo_estimado_min"),
            "fecha_programada": doc.get("fecha_programada"),
            "hora_programada": doc.get("hora_programada"),
            # Los documentos anteriores no tienen fecha original: nunca se reprogramaron.
            "fecha_original": doc.get("fecha_original") or doc.get("fecha_programada"),
            "prioridad": prioridad,
            "peso_prioridad": Prioridad(prioridad).peso,
            "estado": doc.get("estado", EstadoActividad.PENDIENTE.value),
            "reprogramada": bool(reprogramaciones),
            "reprogramaciones": reprogramaciones,
            "cancelacion": doc.get("cancelacion"),
            "fecha_no_realizada": doc.get("fecha_no_realizada"),
        }
