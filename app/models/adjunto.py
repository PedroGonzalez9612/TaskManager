"""Adjunto de la información de la actividad (alcance, Sección 5.1): un manual, un plano o una foto de
referencia que el Administrador deja para hacer el trabajo. Pertenece a la actividad, no a una
ejecución (a diferencia de la evidencia), y no se borra. El contenido lo guarda el repositorio."""
from app.models.evidencia import TAMANO_MAXIMO, TipoEvidencia, limpiar_nombre
from app.utils.archivos import detectar_tipo_documento, es_imagen
from app.utils.errors import ValidationError

MAXIMO_POR_ACTIVIDAD = 5


class Adjunto:
    def __init__(self, actividad_id, empresa_id, autor_id, nombre, contenido_tipo, tamano, fecha, id=None):
        self.id = id
        self.actividad_id = actividad_id
        self.empresa_id = empresa_id
        self.autor_id = autor_id
        self.nombre = nombre
        self.contenido_tipo = contenido_tipo
        self.tamano = tamano
        self.fecha = fecha

    @classmethod
    def desde_archivo(cls, contenido: bytes, nombre, actividad_id: str, solicitante: dict, ahora) -> "Adjunto":
        """Valida el archivo que llegó. Las mismas reglas que la evidencia: PDF o imagen, hasta 5 MB."""
        if not contenido:
            raise ValidationError("Selecciona un archivo")
        if len(contenido) > TAMANO_MAXIMO:
            raise ValidationError("Cada archivo puede pesar como máximo 5 MB")
        tipo = detectar_tipo_documento(contenido)
        if not tipo:
            raise ValidationError("Solo se aceptan imágenes (JPG, PNG o WEBP) y documentos PDF")
        return cls(actividad_id, solicitante["empresa_id"], solicitante["id"], limpiar_nombre(nombre), tipo,
                   len(contenido), ahora)

    @property
    def tipo(self) -> TipoEvidencia:
        """FOTO se muestra en miniatura; ADJUNTO se abre aparte (como en la evidencia)."""
        return TipoEvidencia.FOTO if es_imagen(self.contenido_tipo) else TipoEvidencia.ADJUNTO

    def to_dict(self) -> dict:
        return {
            "actividad_id": self.actividad_id,
            "empresa_id": self.empresa_id,
            "autor_id": self.autor_id,
            "nombre": self.nombre,
            "contenido_tipo": self.contenido_tipo,
            "tamano": self.tamano,
            "fecha": self.fecha,
        }

    def presentar(self) -> dict:
        return {"id": self.id, "tipo": self.tipo.value, "nombre": self.nombre,
                "contenido_tipo": self.contenido_tipo, "tamano": self.tamano}

    @classmethod
    def desde_documento(cls, doc: dict) -> "Adjunto":
        return cls(doc["actividad_id"], doc["empresa_id"], doc.get("autor_id"), doc["nombre"],
                   doc["contenido_tipo"], doc["tamano"], doc.get("fecha"), id=str(doc["_id"]))
