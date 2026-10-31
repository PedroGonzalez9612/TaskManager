from app.models.enums import EstadoReporte
from app.utils.errors import ValidationError

TITULO_MAXIMO = 120
TEXTO_MAXIMO = 1000
TIEMPO_ESTIMADO_MAXIMO_MIN = 24 * 60


def _texto(valor, obligatorio: str = None, maximo: int = TEXTO_MAXIMO):
    """El texto sin espacios de más. Si es obligatorio y viene vacío, el mensaje dice cuál falta."""
    texto = " ".join(str(valor or "").split())
    if not texto:
        if obligatorio:
            raise ValidationError(obligatorio)
        return None
    if len(texto) > maximo:
        raise ValidationError(f"El texto no puede pasar de {maximo} caracteres")
    return texto


def _tiempo_estimado(valor):
    if valor in (None, ""):
        return None
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValidationError("El tiempo estimado debe ser un número entero de minutos")
    if not 1 <= valor <= TIEMPO_ESTIMADO_MAXIMO_MIN:
        raise ValidationError("El tiempo estimado debe estar entre 1 minuto y 24 horas")
    return valor


class Revision:
    """Qué decidió el Administrador sobre el reporte, quién y cuándo. No se modifica."""

    def __init__(self, autor_id, fecha, motivo=None, actividad_id=None):
        self.autor_id = autor_id
        self.fecha = fecha
        self.motivo = motivo                # Solo si se descartó.
        self.actividad_id = actividad_id    # Solo si se convirtió.

    def to_dict(self) -> dict:
        return {"autor_id": self.autor_id, "fecha": self.fecha, "motivo": self.motivo,
                "actividad_id": self.actividad_id}

    @classmethod
    def desde_documento(cls, doc: dict) -> "Revision":
        return cls(doc.get("autor_id"), doc["fecha"], doc.get("motivo"), doc.get("actividad_id"))


class Reporte:
    """Trabajo que otra área le pidió directamente al Operario y que él reporta (alcance, Sección 5.1).

    Mientras está por revisar no es trabajo del día: no entra en la programación ni en la carga. El
    Administrador lo convierte en actividad o lo descarta con un motivo; después ya no cambia."""

    def __init__(self, empresa_id, operario_id, titulo, pedido_por, fecha, detalle=None,
                 tiempo_estimado_min=None, estado=EstadoReporte.PENDIENTE, revision=None, id=None):
        self.id = id
        self.empresa_id = empresa_id
        self.operario_id = operario_id
        self.titulo = _texto(titulo, "Escribe qué te pidieron", TITULO_MAXIMO)
        self.pedido_por = _texto(pedido_por, "Escribe quién te lo pidió", TITULO_MAXIMO)
        self.detalle = _texto(detalle)
        self.tiempo_estimado_min = _tiempo_estimado(tiempo_estimado_min)
        self.fecha = fecha                  # Cuándo lo reportó, con la hora del servidor.
        self.estado = EstadoReporte(estado)
        self.revision = revision

    def convertir(self, actividad_id, autor_id, ahora) -> None:
        """El Administrador creó una actividad con lo reportado."""
        self.exigir_por_revisar()
        self.estado = EstadoReporte.CONVERTIDO
        self.revision = Revision(autor_id, ahora, actividad_id=actividad_id)

    def descartar(self, motivo, autor_id, ahora) -> None:
        self.exigir_por_revisar()
        motivo = _texto(motivo, "Indica por qué descartas el reporte")
        self.estado = EstadoReporte.DESCARTADO
        self.revision = Revision(autor_id, ahora, motivo=motivo)

    def exigir_por_revisar(self) -> None:
        if self.estado != EstadoReporte.PENDIENTE:
            raise ValidationError("Este reporte ya se revisó")

    def to_dict(self) -> dict:
        return {
            "empresa_id": self.empresa_id,
            "operario_id": self.operario_id,
            "titulo": self.titulo,
            "pedido_por": self.pedido_por,
            "detalle": self.detalle,
            "tiempo_estimado_min": self.tiempo_estimado_min,
            "fecha": self.fecha,
            "estado": self.estado.value,
            "revision": self.revision.to_dict() if self.revision else None,
        }

    @classmethod
    def desde_documento(cls, doc: dict) -> "Reporte":
        revision = doc.get("revision")
        return cls(
            id=str(doc["_id"]),
            empresa_id=doc["empresa_id"],
            operario_id=doc["operario_id"],
            titulo=doc["titulo"],
            pedido_por=doc["pedido_por"],
            fecha=doc["fecha"],
            detalle=doc.get("detalle"),
            tiempo_estimado_min=doc.get("tiempo_estimado_min"),
            estado=doc.get("estado", EstadoReporte.PENDIENTE.value),
            revision=Revision.desde_documento(revision) if revision else None,
        )
