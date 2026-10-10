from typing import NamedTuple

from app.models.enums import MOTIVOS_DEVOLUCION, MOTIVOS_PAUSA_FIJOS, TipoCatalogo
from app.utils.errors import NotFoundError, ValidationError

OPCION_OTRO = "Otro"

# Las tres listas de motivos que se pueden consultar. Las de pausa y cancelación son catálogos de
# la empresa (TipoCatalogo); la de devolución es fija y no se guarda en la base de datos.
MOTIVO_PAUSA = TipoCatalogo.MOTIVO_PAUSA.value
MOTIVO_CANCELACION = TipoCatalogo.MOTIVO_CANCELACION.value
MOTIVO_DEVOLUCION = "MOTIVO_DEVOLUCION"

# Lo que cada lista trae siempre, antes de lo que haya escrito la empresa.
_MOTIVOS_FIJOS = {
    MOTIVO_PAUSA: MOTIVOS_PAUSA_FIJOS,
    MOTIVO_CANCELACION: (),
    MOTIVO_DEVOLUCION: MOTIVOS_DEVOLUCION,
}
# Las listas que se van llenando con lo que se escribe en "Otro".
_TIPOS_QUE_SE_LLENAN = (MOTIVO_PAUSA, MOTIVO_CANCELACION)


def _clave(texto) -> str:
    """Para comparar textos sin distinguir mayúsculas ni espacios de más."""
    return " ".join(str(texto or "").split()).lower()


class MotivoElegido(NamedTuple):
    texto: str        # El motivo que se guarda.
    escrito: bool     # True si la persona lo escribió en "Otro" (no lo eligió de la lista).


def resolver_motivo(motivo, detalle=None) -> MotivoElegido:
    """Regla única del motivo al pausar, cancelar o devolver (alcance, Sección 5.1).

    El cliente manda la opción elegida en "motivo" y, si eligió "Otro", lo que escribió en
    "detalle". Con "Otro" se guarda el texto escrito, que es obligatorio. Con cualquier otra
    opción se guarda la opción y el detalle se ignora. Que el motivo no esté vacío lo exige la
    clase que lo recibe (Pausa, Cancelacion, Devolucion), cada una con su mensaje."""
    motivo = " ".join(str(motivo or "").split())
    if _clave(motivo) != _clave(OPCION_OTRO):
        return MotivoElegido(motivo, False)
    detalle = " ".join(str(detalle or "").split())
    if not detalle or _clave(detalle) == _clave(OPCION_OTRO):
        raise ValidationError('Si eliges "Otro", escribe el motivo')
    return MotivoElegido(detalle, True)


class CatalogoService:
    """Listas desplegables de motivos por empresa (alcance, Sección 5.1). El repositorio solo guarda
    lo que escribieron las personas; los motivos fijos y la opción "Otro" los agrega este servicio."""

    def __init__(self, catalogo_repository):
        self.catalogo_repository = catalogo_repository

    def listar(self, solicitante: dict, tipo: str) -> list:
        """Los textos de la lista, en el orden en que se muestran: primero los fijos, después los
        de la empresa (en orden alfabético) y "Otro" al final."""
        if tipo not in _MOTIVOS_FIJOS:
            raise NotFoundError("Esa lista no existe")
        motivos = list(_MOTIVOS_FIJOS[tipo])
        if tipo in _TIPOS_QUE_SE_LLENAN:
            motivos += self.catalogo_repository.listar(solicitante["empresa_id"], tipo)

        lista, vistos = [], {_clave(OPCION_OTRO)}
        for motivo in motivos:
            if _clave(motivo) not in vistos:
                vistos.add(_clave(motivo))
                lista.append(motivo)
        return lista + [OPCION_OTRO]

    def registrar_motivo(self, empresa_id: str, tipo: str, elegido: MotivoElegido) -> None:
        """Agrega a la lista de la empresa el motivo que alguien escribió en "Otro". No hace nada
        si lo eligió de la lista, si la lista es fija o si escribió uno de los motivos fijos.
        Que no se repita (con otras mayúsculas) lo garantiza el repositorio."""
        if not elegido.escrito or tipo not in _TIPOS_QUE_SE_LLENAN:
            return
        if _clave(elegido.texto) in {_clave(fijo) for fijo in _MOTIVOS_FIJOS[tipo]}:
            return
        self.catalogo_repository.registrar(empresa_id, tipo, elegido.texto)
