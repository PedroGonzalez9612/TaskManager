"""Información de la actividad (alcance, Sección 5.1): lo que el Administrador deja para hacer el
trabajo, por bloques. Se diferencia de la evidencia, que deja el Operario al terminar.

El Administrador elige qué bloques lleva cada actividad. La actividad está "Lista para iniciar"
cuando cada bloque elegido tiene contenido; si no, le falta información (es un aviso, no un bloqueo).
Los archivos del bloque de adjuntos se guardan aparte (clase Adjunto): aquí solo se cuentan."""
from enum import Enum

from app.models.enums import TipoCatalogo
from app.utils.errors import ValidationError

MAXIMO_VALORES_POR_BLOQUE = 20
LARGO_MAXIMO_VALOR = 200


class BloqueInformacion(str, Enum):
    PASOS = "PASOS"
    HERRAMIENTAS = "HERRAMIENTAS"
    EQUIPO = "EQUIPO"
    PRECAUCIONES = "PRECAUCIONES"
    CONTACTO = "CONTACTO"
    ADJUNTOS = "ADJUNTOS"

    @property
    def nombre(self) -> str:
        """Como se llama en las pantallas."""
        return _NOMBRES[self]

    @property
    def campo(self):
        """El campo del documento con sus valores; None para los adjuntos, que se guardan aparte."""
        return _CAMPOS.get(self)

    @property
    def catalogo(self):
        """El catálogo de la empresa que sugiere sus valores; None si el bloque no tiene catálogo."""
        return _CATALOGOS.get(self)


_NOMBRES = {
    BloqueInformacion.PASOS: "Pasos",
    BloqueInformacion.HERRAMIENTAS: "Herramientas y materiales",
    BloqueInformacion.EQUIPO: "Equipo",
    BloqueInformacion.PRECAUCIONES: "Precauciones de seguridad",
    BloqueInformacion.CONTACTO: "Contacto",
    BloqueInformacion.ADJUNTOS: "Adjuntos",
}
_CAMPOS = {
    BloqueInformacion.PASOS: "pasos",
    BloqueInformacion.HERRAMIENTAS: "herramientas",
    BloqueInformacion.EQUIPO: "equipo",
    BloqueInformacion.PRECAUCIONES: "precauciones",
    BloqueInformacion.CONTACTO: "contacto",
}
# Los pasos son propios de cada actividad: no se sugieren de una actividad a otra.
_CATALOGOS = {
    BloqueInformacion.HERRAMIENTAS: TipoCatalogo.HERRAMIENTA,
    BloqueInformacion.EQUIPO: TipoCatalogo.EQUIPO,
    BloqueInformacion.PRECAUCIONES: TipoCatalogo.PRECAUCION,
    BloqueInformacion.CONTACTO: TipoCatalogo.CONTACTO,
}


def _limpiar_valores(valores, nombre_bloque: str) -> list:
    """Textos sin espacios de más, sin vacíos y sin repetidos (sin distinguir mayúsculas), en el
    orden en que llegaron: en los pasos el orden importa."""
    if valores is None:
        return []
    if not isinstance(valores, list):
        raise ValidationError(f"{nombre_bloque}: debe ser una lista")
    limpios, vistos = [], set()
    for valor in valores:
        texto = " ".join(str(valor or "").split())
        if not texto or texto.lower() in vistos:
            continue
        if len(texto) > LARGO_MAXIMO_VALOR:
            raise ValidationError(f"{nombre_bloque}: cada elemento tiene como máximo {LARGO_MAXIMO_VALOR} caracteres")
        vistos.add(texto.lower())
        limpios.append(texto)
    if len(limpios) > MAXIMO_VALORES_POR_BLOQUE:
        raise ValidationError(f"{nombre_bloque}: como máximo {MAXIMO_VALORES_POR_BLOQUE} elementos")
    return limpios


class InformacionActividad:
    def __init__(self, bloques=(), valores=None):
        self.bloques = list(bloques)    # Los bloques que el Administrador eligió, en el orden de BloqueInformacion.
        self.valores = {bloque: list((valores or {}).get(bloque, [])) for bloque in self.bloques if bloque.campo}

    @classmethod
    def desde_datos(cls, datos) -> "InformacionActividad":
        """Valida lo que mandó el Administrador. Solo se guarda el contenido de los bloques elegidos:
        si quita un bloque, su contenido se va con él."""
        if datos is None:
            return cls()
        if not isinstance(datos, dict):
            raise ValidationError("La información de la actividad no es válida")
        pedidos = datos.get("bloques") or []
        if not isinstance(pedidos, list):
            raise ValidationError("Los bloques de información deben ser una lista")
        try:
            elegidos = {BloqueInformacion(bloque) for bloque in pedidos}
        except ValueError:
            raise ValidationError("Uno de los bloques de información no existe")
        bloques = [bloque for bloque in BloqueInformacion if bloque in elegidos]
        valores = {
            bloque: _limpiar_valores(datos.get(bloque.campo), bloque.nombre)
            for bloque in bloques if bloque.campo
        }
        return cls(bloques, valores)

    def faltantes(self, cantidad_adjuntos: int = 0) -> list:
        """Los bloques elegidos que todavía no tienen contenido."""
        return [
            bloque for bloque in self.bloques
            if (cantidad_adjuntos == 0 if bloque == BloqueInformacion.ADJUNTOS else not self.valores[bloque])
        ]

    def lista_para_iniciar(self, cantidad_adjuntos: int = 0) -> bool:
        return not self.faltantes(cantidad_adjuntos)

    def valores_de_catalogo(self) -> list:
        """(catálogo, valor) de lo escrito en los bloques que se sugieren, para guardarlo en la lista
        de la empresa."""
        return [
            (bloque.catalogo, valor)
            for bloque in self.bloques if bloque.catalogo
            for valor in self.valores[bloque]
        ]

    def to_dict(self) -> dict:
        documento = {"bloques": [bloque.value for bloque in self.bloques]}
        for bloque in BloqueInformacion:
            if bloque.campo:
                documento[bloque.campo] = self.valores.get(bloque, [])
        return documento

    @classmethod
    def desde_documento(cls, doc) -> "InformacionActividad":
        """Las actividades anteriores a la información por bloques no tienen ninguno elegido."""
        doc = doc or {}
        bloques = [BloqueInformacion(bloque) for bloque in doc.get("bloques", [])]
        return cls(bloques, {bloque: doc.get(bloque.campo, []) for bloque in bloques if bloque.campo})
