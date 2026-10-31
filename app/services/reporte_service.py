from datetime import datetime, timezone

from app.models.enums import EstadoReporte, Rol
from app.models.reporte import Reporte
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError

# El Operario ve en Hoy solo sus reportes más recientes.
REPORTES_RECIENTES = 10
# Si dos Administradores convierten el mismo reporte a la vez, la actividad del segundo se cancela
# con este motivo (nada se borra).
MOTIVO_REPORTE_YA_REVISADO = "El reporte ya se había revisado"


class ReporteService:
    """Reportes de actividad (alcance, Sección 5.1): el Operario reporta un trabajo que otra área le
    pidió directamente, y el Administrador de su empresa lo convierte en actividad o lo descarta."""

    def __init__(self, reporte_repository, usuario_repository, actividad_repository, actividad_service, reloj=None):
        # La hora de todo evento la pone el servidor. Las pruebas pasan un reloj que ellas controlan.
        self.reloj = reloj or (lambda: datetime.now(timezone.utc))
        self.reporte_repository = reporte_repository
        self.usuario_repository = usuario_repository
        self.actividad_repository = actividad_repository
        # Convertir un reporte es crear una actividad, con las mismas validaciones de siempre.
        self.actividad_service = actividad_service

    def reportar(self, data: dict, solicitante: dict) -> dict:
        if solicitante["rol"] != Rol.OPERARIO.value:
            raise ProhibidoError("Solo un operario reporta una actividad")
        reporte = Reporte(
            empresa_id=solicitante["empresa_id"],
            operario_id=solicitante["id"],
            titulo=data.get("titulo"),
            pedido_por=data.get("pedido_por"),
            detalle=data.get("detalle"),
            tiempo_estimado_min=data.get("tiempo_estimado_min"),
            fecha=self.reloj(),
        )
        reporte_id = self.reporte_repository.insert(reporte.to_dict())
        return self._presentar([self.reporte_repository.find_by_id(reporte_id)])[0]

    def listar(self, solicitante: dict, estado: str = None) -> list:
        """El Administrador ve los de su empresa (con "estado", solo los de ese estado); el Operario,
        sus reportes más recientes."""
        if solicitante["rol"] == Rol.OPERARIO.value:
            docs = self.reporte_repository.find_de_operario(solicitante["id"], REPORTES_RECIENTES)
        else:
            if estado and estado not in EstadoReporte.__members__:
                raise ValidationError("El estado del reporte no es válido")
            docs = self.reporte_repository.find_de_empresa(solicitante["empresa_id"], estado)
        return self._presentar(docs)

    def convertir(self, reporte_id: str, data: dict, solicitante: dict) -> dict:
        """Crea la actividad con los datos del formulario (ya llenos con lo reportado) y deja el
        reporte como Convertido. Devuelve la actividad creada."""
        reporte = self._por_revisar(reporte_id, solicitante)
        reporte.exigir_por_revisar()    # Antes de crear la actividad, para no dejar una que sobre.
        actividad = self.actividad_service.crear_actividad(data, solicitante)
        reporte.convertir(actividad["id"], solicitante["id"], self.reloj())
        if not self._guardar_revision(reporte):
            # Otro Administrador lo revisó mientras tanto: la actividad que sobra se cancela.
            self.actividad_service.cancelar(actividad["id"], solicitante, MOTIVO_REPORTE_YA_REVISADO)
            raise ValidationError("Otro Administrador revisó este reporte mientras tanto")
        return actividad

    def descartar(self, reporte_id: str, motivo, solicitante: dict) -> dict:
        reporte = self._por_revisar(reporte_id, solicitante)
        reporte.descartar(motivo, solicitante["id"], self.reloj())
        if not self._guardar_revision(reporte):
            raise ValidationError("Otro Administrador revisó este reporte mientras tanto")
        return self._presentar([self.reporte_repository.find_by_id(reporte_id)])[0]

    def _por_revisar(self, reporte_id: str, solicitante: dict) -> Reporte:
        """El reporte, si es de la empresa del Administrador. Que siga por revisar lo valida la clase."""
        if solicitante["rol"] != Rol.ADMINISTRADOR.value:
            raise ProhibidoError("Solo el Administrador revisa los reportes")
        doc = self.reporte_repository.find_by_id(reporte_id)
        if not doc or doc["empresa_id"] != solicitante["empresa_id"]:
            raise NotFoundError("El reporte no existe")
        return Reporte.desde_documento(doc)

    def _guardar_revision(self, reporte: Reporte) -> bool:
        """Guarda la revisión solo si el reporte sigue por revisar: Mongo comprueba y escribe en un
        solo paso, así dos revisiones a la vez no se pisan."""
        cambios = {"estado": reporte.estado.value, "revision": reporte.revision.to_dict()}
        return self.reporte_repository.actualizar_si(reporte.id, {"estado": EstadoReporte.PENDIENTE.value}, cambios)

    def _presentar(self, docs: list) -> list:
        """Cada reporte con el nombre de quien lo reportó y, si se convirtió, el código de la actividad."""
        nombres = {}
        presentados = []
        for doc in docs:
            reporte = Reporte.desde_documento(doc)
            if reporte.operario_id not in nombres:
                usuario = self.usuario_repository.find_by_id(reporte.operario_id) or {}
                nombres[reporte.operario_id] = usuario.get("nombre")
            datos = {"id": reporte.id, **reporte.to_dict(), "operario_nombre": nombres[reporte.operario_id]}
            if reporte.revision and reporte.revision.actividad_id:
                actividad = self.actividad_repository.find_by_id(reporte.revision.actividad_id) or {}
                datos["revision"]["actividad_codigo"] = actividad.get("codigo")
            presentados.append(datos)
        return presentados
