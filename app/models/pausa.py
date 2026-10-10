from datetime import timezone

from app.utils.errors import ValidationError


def en_utc(fecha):
    """MongoDB devuelve las fechas sin zona, aunque están en UTC. Aquí se les pone, para poder restarlas."""
    if fecha is not None and fecha.tzinfo is None:
        return fecha.replace(tzinfo=timezone.utc)
    return fecha


def minutos_entre(inicio, fin) -> float:
    return max(0.0, (en_utc(fin) - en_utc(inicio)).total_seconds() / 60)


class Pausa:
    """Una interrupción dentro de una ejecución. Cada pausa guarda su propio motivo (alcance, Sección 6.1)."""

    def __init__(self, motivo, inicio, fin=None):
        motivo = (motivo or "").strip()
        if not motivo:
            raise ValidationError("Indica el motivo de la pausa")
        self.motivo = motivo
        self.inicio = inicio
        self.fin = fin

    @property
    def esta_abierta(self) -> bool:
        return self.fin is None

    def cerrar(self, ahora) -> None:
        if not self.esta_abierta:
            raise ValidationError("Esta pausa ya terminó")
        self.fin = ahora

    def duracion_min(self, ahora) -> float:
        """Minutos que duró la pausa. Si sigue abierta, se cuenta hasta "ahora"."""
        return minutos_entre(self.inicio, self.fin or ahora)

    def to_dict(self) -> dict:
        return {"motivo": self.motivo, "inicio": self.inicio, "fin": self.fin}

    @classmethod
    def desde_documento(cls, doc: dict) -> "Pausa":
        return cls(motivo=doc["motivo"], inicio=doc["inicio"], fin=doc.get("fin"))
