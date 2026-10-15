"""Evidencia de la ejecución (alcance, Sección 5.1): las fotos y los adjuntos que el operario deja al
finalizar una actividad. La observación es un dato de la ejecución; esta clase es para los archivos.

Pertenece a una ejecución (operario + actividad) y no se borra. La clase solo guarda los datos del
archivo; el contenido (los bytes) lo guarda y lo entrega el repositorio."""
import ntpath
from enum import Enum

from app.utils.archivos import detectar_tipo_documento, es_imagen
from app.utils.errors import ValidationError

TAMANO_MAXIMO = 5 * 1024 * 1024      # 5 MB por archivo.
MAXIMO_POR_EJECUCION = 5
LARGO_MAXIMO_NOMBRE = 120
NOMBRE_POR_DEFECTO = "archivo"


class TipoEvidencia(str, Enum):
    FOTO = "FOTO"           # Una imagen: se muestra en miniatura.
    ADJUNTO = "ADJUNTO"     # Un documento (PDF): se abre aparte.


def limpiar_nombre(nombre) -> str:
    """Solo el nombre del archivo, sin la carpeta del equipo de quien lo subió y con un largo máximo."""
    nombre = ntpath.basename(str(nombre or "")).strip()
    return (nombre or NOMBRE_POR_DEFECTO)[:LARGO_MAXIMO_NOMBRE]


class Evidencia:
    def __init__(self, ejecucion_id, actividad_id, usuario_id, empresa_id, nombre, contenido_tipo, tamano,
                 fecha, id=None):
        self.id = id
        self.ejecucion_id = ejecucion_id
        self.actividad_id = actividad_id
        self.usuario_id = usuario_id
        self.empresa_id = empresa_id
        self.nombre = nombre
        self.contenido_tipo = contenido_tipo
        self.tamano = tamano
        self.fecha = fecha

    @classmethod
    def desde_archivo(cls, contenido: bytes, nombre, ejecucion, empresa_id: str, ahora) -> "Evidencia":
        """Valida el archivo que llegó y crea su evidencia. El tipo se reconoce por el contenido."""
        if not contenido:
            raise ValidationError("Selecciona una foto o un archivo")
        if len(contenido) > TAMANO_MAXIMO:
            raise ValidationError("Cada archivo puede pesar como máximo 5 MB")
        tipo = detectar_tipo_documento(contenido)
        if not tipo:
            raise ValidationError("Solo se aceptan fotos (JPG, PNG o WEBP) y documentos PDF")
        return cls(ejecucion.id, ejecucion.actividad_id, ejecucion.usuario_id, empresa_id,
                   limpiar_nombre(nombre), tipo, len(contenido), ahora)

    @property
    def tipo(self) -> TipoEvidencia:
        return TipoEvidencia.FOTO if es_imagen(self.contenido_tipo) else TipoEvidencia.ADJUNTO

    def to_dict(self) -> dict:
        return {
            "ejecucion_id": self.ejecucion_id,
            "actividad_id": self.actividad_id,
            "usuario_id": self.usuario_id,
            "empresa_id": self.empresa_id,
            "nombre": self.nombre,
            "contenido_tipo": self.contenido_tipo,
            "tamano": self.tamano,
            "fecha": self.fecha,
        }

    def presentar(self) -> dict:
        """Lo que va a la interfaz: los datos del archivo, sin su contenido."""
        return {"id": self.id, "tipo": self.tipo.value, "nombre": self.nombre,
                "contenido_tipo": self.contenido_tipo, "tamano": self.tamano}

    @classmethod
    def desde_documento(cls, doc: dict) -> "Evidencia":
        return cls(doc["ejecucion_id"], doc["actividad_id"], doc["usuario_id"], doc["empresa_id"], doc["nombre"],
                   doc["contenido_tipo"], doc["tamano"], doc.get("fecha"), id=str(doc["_id"]))
