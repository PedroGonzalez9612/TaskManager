from datetime import datetime, timedelta

from app.utils.errors import ValidationError
from app.utils.fechas import validar_hora
from app.utils.reloj import momento_local

MINUTOS_DEL_DIA = 24 * 60


def _minutos(hora: str) -> int:
    horas, minutos = map(int, hora.split(":"))
    return horas * 60 + minutos


class Turno:
    """Un turno del catálogo de la empresa (alcance, Sección 5.1): nombre, hora de inicio, hora de
    fin y descanso. Si la hora de fin es menor que la de inicio, el turno termina al día siguiente;
    la jornada pertenece al día en que el turno empieza."""

    def __init__(self, nombre, hora_inicio, hora_fin, descanso_min, empresa_id, id=None):
        nombre = (nombre or "").strip()
        if not nombre:
            raise ValidationError("El turno necesita un nombre")
        self.id = id
        self.nombre = nombre
        self.hora_inicio = validar_hora(hora_inicio, "La hora de inicio")
        self.hora_fin = validar_hora(hora_fin, "La hora de fin")
        if self.hora_inicio == self.hora_fin:
            raise ValidationError("La hora de fin debe ser distinta de la de inicio")
        try:
            self.descanso_min = int(descanso_min or 0)
        except (TypeError, ValueError):
            raise ValidationError("El descanso debe ser un número entero de minutos")
        if not 0 <= self.descanso_min < self.duracion_min:
            raise ValidationError("El descanso no puede ser negativo ni ocupar todo el turno")
        self.empresa_id = empresa_id

    @property
    def duracion_min(self) -> int:
        return (_minutos(self.hora_fin) - _minutos(self.hora_inicio)) % MINUTOS_DEL_DIA

    @property
    def capacidad_min(self) -> int:
        """Tiempo de trabajo disponible en la jornada: duración del turno menos el descanso."""
        return self.duracion_min - self.descanso_min

    def inicio_en(self, fecha: str, zona=None) -> datetime:
        """Cuándo empieza el turno en la jornada "fecha", como momento en UTC."""
        return momento_local(fecha, self.hora_inicio, zona)

    def fin_en(self, fecha: str, zona=None) -> datetime:
        """Cuándo termina el turno de la jornada "fecha" (puede ser el día siguiente), en UTC."""
        return self.inicio_en(fecha, zona) + timedelta(minutes=self.duracion_min)

    def to_dict(self) -> dict:
        return {
            "nombre": self.nombre, "hora_inicio": self.hora_inicio, "hora_fin": self.hora_fin,
            "descanso_min": self.descanso_min, "empresa_id": self.empresa_id,
        }

    @classmethod
    def desde_documento(cls, doc: dict) -> "Turno":
        return cls(doc["nombre"], doc["hora_inicio"], doc["hora_fin"], doc.get("descanso_min", 0),
                   doc.get("empresa_id"), id=str(doc["_id"]))

    def presentar(self) -> dict:
        return {"id": self.id, **self.to_dict(), "duracion_min": self.duracion_min, "capacidad_min": self.capacidad_min}


class AsignacionTurno:
    """El turno que tiene un operario desde una fecha. Cambiar de turno crea una asignación nueva y
    conserva las anteriores, para calcular los periodos pasados con el turno que regía entonces."""

    def __init__(self, usuario_id, turno_id, desde, asignado_por_id=None, fecha_registro=None, id=None):
        self.id = id
        self.usuario_id = usuario_id
        self.turno_id = turno_id
        self.desde = desde                      # "AAAA-MM-DD": primera jornada con este turno.
        self.asignado_por_id = asignado_por_id
        self.fecha_registro = fecha_registro

    def to_dict(self) -> dict:
        return {
            "usuario_id": self.usuario_id, "turno_id": self.turno_id, "desde": self.desde,
            "asignado_por_id": self.asignado_por_id, "fecha_registro": self.fecha_registro,
        }

    @classmethod
    def desde_documento(cls, doc: dict) -> "AsignacionTurno":
        return cls(doc["usuario_id"], doc["turno_id"], doc["desde"], doc.get("asignado_por_id"),
                   doc.get("fecha_registro"), id=str(doc["_id"]))


def turno_vigente(asignaciones: list, fecha: str):
    """De las asignaciones de turno de un operario, la que rige en la jornada "fecha": la más reciente
    cuyo "desde" no es posterior a esa fecha. None si no tenía turno ese día."""
    vigentes = [a for a in asignaciones if a.desde <= fecha]
    return max(vigentes, key=lambda a: (a.desde, a.fecha_registro or datetime.min), default=None)
