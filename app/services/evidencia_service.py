"""Evidencia de la ejecución (alcance, Sección 5.1): el operario sube fotos y adjuntos de su trabajo
mientras la actividad está en curso o pausada (la interfaz lo hace justo antes de finalizar), y
los ven él y el Administrador de su empresa. Nada se borra."""
from datetime import datetime, timezone

from app.models.ejecucion import Ejecucion
from app.models.enums import Rol
from app.models.evidencia import MAXIMO_POR_EJECUCION, Evidencia
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError

NO_EXISTE = "La evidencia no existe"


class EvidenciaService:
    def __init__(self, evidencia_repository, ejecucion_repository, actividad_repository, asignacion_repository,
                 reloj=None):
        self.evidencia_repository = evidencia_repository
        self.ejecucion_repository = ejecucion_repository
        self.actividad_repository = actividad_repository
        self.asignacion_repository = asignacion_repository
        # La hora la pone el servidor. Las pruebas pasan un reloj que ellas controlan.
        self.reloj = reloj or (lambda: datetime.now(timezone.utc))

    # ---------- Operario ----------

    def agregar(self, actividad_id: str, solicitante: dict, contenido: bytes, nombre) -> dict:
        """Agrega una foto o un adjunto a la ejecución del operario en esa actividad."""
        if solicitante["rol"] != Rol.OPERARIO.value:
            raise ProhibidoError("Solo el operario deja evidencia de su trabajo")
        ejecucion = self._ejecucion_abierta(actividad_id, solicitante)
        if self.evidencia_repository.contar_de_ejecucion(ejecucion.id) >= MAXIMO_POR_EJECUCION:
            raise ValidationError(f"Puedes dejar como máximo {MAXIMO_POR_EJECUCION} archivos por actividad")

        evidencia = Evidencia.desde_archivo(contenido, nombre, ejecucion, solicitante["empresa_id"], self.reloj())
        evidencia.id = self.evidencia_repository.insertar(evidencia.to_dict(), contenido)
        return evidencia.presentar()

    # ---------- Consultar (Operario y Administrador) ----------

    def obtener(self, actividad_id: str, evidencia_id: str, solicitante: dict) -> tuple:
        """(contenido, tipo, nombre) del archivo. El Operario ve solo la suya; el Administrador, las
        de su empresa. A cualquier otro se le responde que no existe, sin decir de quién es."""
        doc = self.evidencia_repository.find_datos(evidencia_id)
        if not doc or doc["actividad_id"] != actividad_id or not self._puede_ver(doc, solicitante):
            raise NotFoundError(NO_EXISTE)
        contenido = self.evidencia_repository.find_contenido(evidencia_id)
        if contenido is None:
            raise NotFoundError(NO_EXISTE)
        return contenido, doc["contenido_tipo"], doc["nombre"]

    def de_ejecuciones(self, ejecucion_ids) -> dict:
        """{id de la ejecución: [evidencias presentadas]}, en una sola consulta."""
        por_ejecucion = {}
        for doc in self.evidencia_repository.find_de_ejecuciones(ejecucion_ids):
            evidencia = Evidencia.desde_documento(doc)
            por_ejecucion.setdefault(evidencia.ejecucion_id, []).append(evidencia.presentar())
        return por_ejecucion

    # ---------- Apoyo ----------

    @staticmethod
    def _puede_ver(doc: dict, solicitante: dict) -> bool:
        if solicitante["rol"] == Rol.OPERARIO.value:
            return doc["usuario_id"] == solicitante["id"]
        return solicitante["rol"] == Rol.ADMINISTRADOR.value and doc["empresa_id"] == solicitante["empresa_id"]

    def _ejecucion_abierta(self, actividad_id: str, solicitante: dict) -> Ejecucion:
        """La ejecución del operario en esa actividad, si está en curso o pausada."""
        actividad = self.actividad_repository.find_by_id(actividad_id)
        if not actividad or actividad.get("empresa_id") != solicitante["empresa_id"]:
            raise NotFoundError("La actividad no existe")
        asignacion = self.asignacion_repository.find_activa(actividad_id, solicitante["id"])
        if not asignacion:
            raise ProhibidoError("Esta actividad no está asignada a ti")
        doc = self.ejecucion_repository.find_by_asignacion(str(asignacion["_id"]))
        ejecucion = Ejecucion.desde_documento(doc) if doc else None
        if not ejecucion or not ejecucion.esta_abierta:
            raise ValidationError("La evidencia se agrega mientras la actividad está en curso o pausada")
        return ejecucion
