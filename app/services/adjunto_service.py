"""Adjuntos de la información de la actividad (alcance, Sección 5.1). Los sube el Administrador
mientras la actividad se puede editar (hasta que alguien la inicie); los ven él y los operarios
asignados. Nada se borra."""
from datetime import datetime, timezone

from app.models.adjunto import MAXIMO_POR_ACTIVIDAD, Adjunto
from app.models.enums import EstadoActividad, Rol
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError

NO_EXISTE = "El adjunto no existe"


class AdjuntoService:
    def __init__(self, adjunto_repository, actividad_repository, asignacion_repository, ejecucion_repository,
                 reloj=None):
        self.adjunto_repository = adjunto_repository
        self.actividad_repository = actividad_repository
        self.asignacion_repository = asignacion_repository
        self.ejecucion_repository = ejecucion_repository
        # La hora la pone el servidor. Las pruebas pasan un reloj que ellas controlan.
        self.reloj = reloj or (lambda: datetime.now(timezone.utc))

    def agregar(self, actividad_id: str, solicitante: dict, contenido: bytes, nombre) -> dict:
        if solicitante["rol"] != Rol.ADMINISTRADOR.value:
            raise ProhibidoError("Solo el Administrador agrega la información de la actividad")
        actividad = self.actividad_repository.find_by_id(actividad_id)
        if not actividad or actividad.get("empresa_id") != solicitante["empresa_id"]:
            raise NotFoundError("La actividad no existe")
        # La misma regla que editar la actividad (alcance, Sección 5.1, reglas de estado).
        if EstadoActividad(actividad.get("estado", EstadoActividad.PENDIENTE.value)).es_final \
                or self.ejecucion_repository.find_by_actividades([actividad_id]):
            raise ValidationError("Esta actividad ya se inició o está cerrada: su información no se cambia")
        if self.adjunto_repository.contar_de_actividad(actividad_id) >= MAXIMO_POR_ACTIVIDAD:
            raise ValidationError(f"Una actividad puede tener como máximo {MAXIMO_POR_ACTIVIDAD} adjuntos")

        adjunto = Adjunto.desde_archivo(contenido, nombre, actividad_id, solicitante, self.reloj())
        adjunto.id = self.adjunto_repository.insertar(adjunto.to_dict(), contenido)
        return adjunto.presentar()

    def obtener(self, actividad_id: str, adjunto_id: str, solicitante: dict) -> tuple:
        """(contenido, tipo, nombre). El Administrador ve los de su empresa; el Operario, los de las
        actividades que tiene asignadas. A cualquier otro se le responde que no existe."""
        doc = self.adjunto_repository.find_datos(adjunto_id)
        if not doc or doc["actividad_id"] != actividad_id or not self._puede_ver(doc, solicitante):
            raise NotFoundError(NO_EXISTE)
        contenido = self.adjunto_repository.find_contenido(adjunto_id)
        if contenido is None:
            raise NotFoundError(NO_EXISTE)
        return contenido, doc["contenido_tipo"], doc["nombre"]

    def de_actividades(self, actividad_ids) -> dict:
        """{id de la actividad: [adjuntos presentados]}, en una sola consulta."""
        por_actividad = {}
        for doc in self.adjunto_repository.find_de_actividades(actividad_ids):
            adjunto = Adjunto.desde_documento(doc)
            por_actividad.setdefault(adjunto.actividad_id, []).append(adjunto.presentar())
        return por_actividad

    def _puede_ver(self, doc: dict, solicitante: dict) -> bool:
        if doc["empresa_id"] != solicitante["empresa_id"]:
            return False
        if solicitante["rol"] == Rol.OPERARIO.value:
            return self.asignacion_repository.existe(doc["actividad_id"], solicitante["id"])
        return solicitante["rol"] == Rol.ADMINISTRADOR.value
