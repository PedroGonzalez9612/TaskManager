"""Constancias de hechos que le ocurren a una actividad o a una asignación: qué pasó, por qué,
quién lo hizo y cuándo. Se guardan dentro de su dueño y nunca se modifican (nada se borra:
alcance, Sección 5.1)."""
from app.utils.errors import ValidationError


def _motivo_obligatorio(motivo, mensaje: str) -> str:
    motivo = (motivo or "").strip()
    if not motivo:
        raise ValidationError(mensaje)
    return motivo


class Devolucion:
    """El operario devolvió la actividad antes de iniciarla."""

    def __init__(self, motivo, fecha):
        self.motivo = _motivo_obligatorio(motivo, "Indica por qué devuelves la actividad")
        self.fecha = fecha

    def to_dict(self) -> dict:
        return {"motivo": self.motivo, "fecha": self.fecha}

    @classmethod
    def desde_documento(cls, doc: dict) -> "Devolucion":
        return cls(motivo=doc["motivo"], fecha=doc["fecha"])


class Cancelacion:
    """El Administrador canceló la actividad."""

    def __init__(self, motivo, autor_id, fecha):
        self.motivo = _motivo_obligatorio(motivo, "Indica el motivo de la cancelación")
        self.autor_id = autor_id
        self.fecha = fecha

    def to_dict(self) -> dict:
        return {"motivo": self.motivo, "autor_id": self.autor_id, "fecha": self.fecha}

    @classmethod
    def desde_documento(cls, doc: dict) -> "Cancelacion":
        return cls(motivo=doc["motivo"], autor_id=doc.get("autor_id"), fecha=doc["fecha"])


class Reprogramacion:
    """La actividad no se terminó en su jornada y pasó a otra."""

    def __init__(self, jornada_origen, jornada_destino, fecha):
        self.jornada_origen = jornada_origen      # "AAAA-MM-DD"
        self.jornada_destino = jornada_destino
        self.fecha = fecha                        # Cuándo lo registró el servidor.

    def to_dict(self) -> dict:
        return {"jornada_origen": self.jornada_origen, "jornada_destino": self.jornada_destino, "fecha": self.fecha}

    @classmethod
    def desde_documento(cls, doc: dict) -> "Reprogramacion":
        return cls(doc["jornada_origen"], doc["jornada_destino"], doc["fecha"])
