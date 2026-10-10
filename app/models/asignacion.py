from datetime import datetime, timezone

from app.models.enums import EstadoAsignacion
from app.models.registros import Devolucion
from app.utils.errors import ValidationError


class Asignacion:
    """Une una actividad con un operario: dice quién responde por ella y desde cuándo.

    Una asignación no se borra. Se cierra cuando el operario devuelve la actividad o cuando el
    Administrador se la retira, y queda como historial. Si después se le vuelve a asignar la misma
    actividad, se crea una asignación nueva."""

    def __init__(self, actividad_id, usuario_id, fecha_asignacion=None, asignada_por_id=None,
                 estado=EstadoAsignacion.ACTIVA, fecha_fin=None, retirada_por_id=None, devolucion=None, id=None):
        self.id = id
        self.actividad_id = actividad_id
        self.usuario_id = usuario_id
        self.fecha_asignacion = fecha_asignacion or datetime.now(timezone.utc)
        self.asignada_por_id = asignada_por_id
        self.estado = EstadoAsignacion(estado)
        self.fecha_fin = fecha_fin
        self.retirada_por_id = retirada_por_id
        self.devolucion = devolucion

    @property
    def esta_activa(self) -> bool:
        return self.estado == EstadoAsignacion.ACTIVA

    def devolver(self, motivo, ahora) -> None:
        """El operario devuelve la actividad. Que todavía no la haya iniciado lo comprueba el servicio,
        porque depende de si existe una ejecución."""
        self._exigir_activa()
        self.devolucion = Devolucion(motivo, ahora)
        self.estado = EstadoAsignacion.DEVUELTA
        self.fecha_fin = ahora

    def retirar(self, autor_id, ahora) -> None:
        """El Administrador le quita la actividad a este operario."""
        self._exigir_activa()
        self.estado = EstadoAsignacion.RETIRADA
        self.fecha_fin = ahora
        self.retirada_por_id = autor_id

    def _exigir_activa(self) -> None:
        if not self.esta_activa:
            raise ValidationError("Esta asignación ya no está activa")

    def to_dict(self):
        return {
            "actividad_id": self.actividad_id,
            "usuario_id": self.usuario_id,
            "fecha_asignacion": self.fecha_asignacion,
            "asignada_por_id": self.asignada_por_id,
            "estado": self.estado.value,
            "fecha_fin": self.fecha_fin,
            "retirada_por_id": self.retirada_por_id,
            "devolucion": self.devolucion.to_dict() if self.devolucion else None,
        }

    @classmethod
    def desde_documento(cls, doc: dict) -> "Asignacion":
        devolucion = doc.get("devolucion")
        return cls(
            id=str(doc["_id"]),
            actividad_id=doc["actividad_id"],
            usuario_id=doc["usuario_id"],
            fecha_asignacion=doc.get("fecha_asignacion"),
            asignada_por_id=doc.get("asignada_por_id"),
            # Las asignaciones anteriores a esta regla no tienen estado: todas estaban activas.
            estado=doc.get("estado", EstadoAsignacion.ACTIVA.value),
            fecha_fin=doc.get("fecha_fin"),
            retirada_por_id=doc.get("retirada_por_id"),
            devolucion=Devolucion.desde_documento(devolucion) if devolucion else None,
        )

    @staticmethod
    def from_doc(doc):
        return {
            "id": str(doc["_id"]),
            "actividad_id": doc["actividad_id"],
            "usuario_id": doc["usuario_id"],
            "fecha_asignacion": doc.get("fecha_asignacion"),
            "estado": doc.get("estado", EstadoAsignacion.ACTIVA.value),
        }
