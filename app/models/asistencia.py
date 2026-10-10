from enum import Enum

from app.models.pausa import en_utc, minutos_entre
from app.utils.errors import ValidationError


class EstadoAsistencia(str, Enum):
    REGISTRADA = "REGISTRADA"      # El operario marcó; el Administrador todavía no la revisa.
    VALIDADA = "VALIDADA"          # El Administrador confirmó las marcas tal como están.
    CORREGIDA = "CORREGIDA"        # El Administrador cambió alguna marca, con su motivo.


class Asistencia:
    """La asistencia de un operario en una jornada (alcance, Sección 5.1): la marca de entrada y la
    de salida, con la hora que pone el servidor. El Administrador la valida o la corrige; una
    corrección conserva las marcas originales y el motivo."""

    def __init__(self, usuario_id, empresa_id, jornada, entrada, salida=None,
                 estado=EstadoAsistencia.REGISTRADA, revision=None, id=None):
        self.id = id
        self.usuario_id = usuario_id
        self.empresa_id = empresa_id
        self.jornada = jornada                  # "AAAA-MM-DD": el día en que empieza su turno.
        self.entrada = entrada
        self.salida = salida
        self.estado = EstadoAsistencia(estado)
        self.revision = revision                # Quién validó o corrigió, cuándo y, si corrigió, qué y por qué.

    @property
    def esta_abierta(self) -> bool:
        """Marcó entrada y todavía no marca salida."""
        return self.salida is None

    def minutos_presente(self, ahora) -> int:
        """Tiempo presente: de la entrada a la salida (o hasta "ahora" si sigue abierta)."""
        return round(minutos_entre(self.entrada, self.salida or ahora))

    def marcar_salida(self, ahora) -> None:
        if not self.esta_abierta:
            raise ValidationError("Ya marcaste la salida de esta jornada")
        if en_utc(ahora) <= en_utc(self.entrada):
            raise ValidationError("La salida debe ser posterior a la entrada")
        self.salida = ahora

    def validar(self, autor_id, ahora) -> None:
        if self.esta_abierta:
            raise ValidationError("Solo se valida una asistencia con entrada y salida")
        self.estado = EstadoAsistencia.VALIDADA
        self.revision = {"autor_id": autor_id, "fecha": ahora}

    def corregir(self, entrada, salida, motivo, autor_id, ahora) -> None:
        """El Administrador corrige las marcas. Exige motivo y conserva las originales."""
        motivo = (motivo or "").strip()
        if not motivo:
            raise ValidationError("Indica el motivo de la corrección")
        if salida is not None and en_utc(salida) <= en_utc(entrada):
            raise ValidationError("La salida debe ser posterior a la entrada")
        self.revision = {
            "autor_id": autor_id, "fecha": ahora, "motivo": motivo,
            "entrada_original": self.entrada, "salida_original": self.salida,
        }
        self.entrada, self.salida = entrada, salida
        self.estado = EstadoAsistencia.CORREGIDA

    def to_dict(self) -> dict:
        return {
            "usuario_id": self.usuario_id, "empresa_id": self.empresa_id, "jornada": self.jornada,
            "entrada": self.entrada, "salida": self.salida, "estado": self.estado.value, "revision": self.revision,
        }

    @classmethod
    def desde_documento(cls, doc: dict) -> "Asistencia":
        return cls(doc["usuario_id"], doc.get("empresa_id"), doc["jornada"], doc["entrada"], doc.get("salida"),
                   doc.get("estado", EstadoAsistencia.REGISTRADA.value), doc.get("revision"), id=str(doc["_id"]))
