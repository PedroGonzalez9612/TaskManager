"""Catálogo de turnos de la empresa y el turno de cada operario (alcance, Sección 5.1).

De aquí sale la capacidad de cada operario en cada jornada (alcance, Sección 5.2): la del turno
vigente ese día o, si no tiene turno, la capacidad provisional."""
from collections import defaultdict

from app.models.enums import Rol
from app.models.turno import AsignacionTurno, Turno, turno_vigente
from app.services.carga_service import CAPACIDAD_JORNADA_MIN
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError
from app.utils.fechas import validar_fecha
from app.utils.reloj import ZONA_POR_DEFECTO, ahora_utc, fecha_local

CAMPOS_TURNO = ("nombre", "hora_inicio", "hora_fin", "descanso_min")


def resumen_turno(turno) -> dict | None:
    """Lo que se muestra del turno junto a un operario: {id, nombre, hora_inicio, hora_fin} o None."""
    if turno is None:
        return None
    return {"id": turno.id, "nombre": turno.nombre, "hora_inicio": turno.hora_inicio, "hora_fin": turno.hora_fin}


class TurnosDeOperarios:
    """Las asignaciones de turno de varios operarios y los turnos a los que apuntan, leídos de una
    vez. Responde qué turno y qué capacidad tiene cada uno en cualquier jornada sin volver a la base."""

    def __init__(self, asignaciones: list, turnos: list):
        self._asignaciones = defaultdict(list)
        for asignacion in asignaciones:
            self._asignaciones[asignacion.usuario_id].append(asignacion)
        self._turnos = {turno.id: turno for turno in turnos}

    def turno_de(self, usuario_id: str, fecha: str):
        """El turno vigente del operario en la jornada "fecha", o None si no tenía."""
        vigente = turno_vigente(self._asignaciones[usuario_id], fecha)
        return self._turnos.get(vigente.turno_id) if vigente else None

    def capacidad_de(self, usuario_id: str, fecha: str) -> int:
        turno = self.turno_de(usuario_id, fecha)
        return turno.capacidad_min if turno else CAPACIDAD_JORNADA_MIN


class TurnoService:
    """El Administrador define los turnos de su empresa y asigna uno a cada operario. Un turno de
    otra empresa no existe para él (404)."""

    def __init__(self, turno_repository, asignacion_turno_repository, usuario_repository,
                 empresa_repository, reloj=None):
        self.turno_repository = turno_repository
        self.asignacion_turno_repository = asignacion_turno_repository
        self.usuario_repository = usuario_repository
        self.empresa_repository = empresa_repository
        # La hora la pone el servidor. Las pruebas pasan un reloj que ellas controlan.
        self.reloj = reloj or ahora_utc

    # ---------- Catálogo de turnos (Administrador) ----------

    def crear_turno(self, data: dict, solicitante: dict) -> dict:
        self._exigir_administrador(solicitante)
        turno = Turno(data.get("nombre"), data.get("hora_inicio"), data.get("hora_fin"),
                      data.get("descanso_min"), solicitante["empresa_id"])
        turno.id = self.turno_repository.insert(turno.to_dict())
        return turno.presentar()

    def listar_turnos(self, solicitante: dict) -> list:
        self._exigir_administrador(solicitante)
        return [Turno.desde_documento(doc).presentar()
                for doc in self.turno_repository.find_by_empresa(solicitante["empresa_id"])]

    def editar_turno(self, turno_id: str, data: dict, solicitante: dict) -> dict:
        """Cambia nombre, horas o descanso. Las asignaciones siguen apuntando al mismo turno."""
        self._exigir_administrador(solicitante)
        actual = self._turno_de_la_empresa(turno_id, solicitante)
        cambios = {campo: data[campo] for campo in CAMPOS_TURNO if campo in data}
        if not cambios:
            raise ValidationError("No hay campos válidos para actualizar")
        datos = {**actual.to_dict(), **cambios}
        turno = Turno(datos["nombre"], datos["hora_inicio"], datos["hora_fin"], datos["descanso_min"],
                      actual.empresa_id, id=actual.id)
        self.turno_repository.update(turno.id, turno.to_dict())
        return turno.presentar()

    # ---------- Turno de cada operario (Administrador) ----------

    def asignar_turno(self, solicitante: dict, operario_id: str, turno_id: str, desde=None) -> dict:
        """Le asigna un turno al operario desde una fecha (por defecto, hoy). Crea una asignación
        nueva y conserva las anteriores: los días previos siguen con el turno que tenían."""
        self._exigir_administrador(solicitante)
        self._operario_de_la_empresa(operario_id, solicitante)
        if not turno_id:
            raise ValidationError("Indica el turno")
        turno = self._turno_de_la_empresa(turno_id, solicitante)
        ahora = self.reloj()
        hoy = fecha_local(ahora, self._zona_de(solicitante["empresa_id"]))
        desde = validar_fecha(desde, "La fecha desde") if desde else hoy
        if desde < hoy:
            raise ValidationError("El turno no se puede asignar desde un día que ya pasó")
        asignacion = AsignacionTurno(operario_id, turno.id, desde, solicitante["id"], ahora)
        asignacion.id = self.asignacion_turno_repository.insert(asignacion.to_dict())
        return {"id": asignacion.id, "operario_id": operario_id, "desde": desde, "turno": turno.presentar()}

    # ---------- Consultas para otros servicios ----------

    def turnos_de_operarios(self, usuario_ids: list) -> TurnosDeOperarios:
        """Los turnos de varios operarios con dos consultas en total, sin importar cuántos sean."""
        asignaciones = [AsignacionTurno.desde_documento(doc)
                        for doc in self.asignacion_turno_repository.find_de_usuarios(usuario_ids)]
        turno_ids = list({asignacion.turno_id for asignacion in asignaciones})
        turnos = [Turno.desde_documento(doc) for doc in self.turno_repository.find_by_ids(turno_ids)] \
            if turno_ids else []
        return TurnosDeOperarios(asignaciones, turnos)

    def turno_de(self, usuario_id: str, fecha: str):
        """El turno vigente del operario en esa jornada, o None si no tiene."""
        return self.turnos_de_operarios([usuario_id]).turno_de(usuario_id, fecha)

    def capacidad_de(self, usuario_id: str, fecha: str) -> int:
        """La capacidad del operario en esa jornada: la de su turno vigente o, sin turno, la provisional."""
        return self.turnos_de_operarios([usuario_id]).capacidad_de(usuario_id, fecha)

    def turnos_de_hoy(self, empresa_id: str, usuario_ids: list) -> dict:
        """{usuario_id: resumen del turno vigente hoy o None}, para la lista de usuarios."""
        hoy = fecha_local(self.reloj(), self._zona_de(empresa_id))
        turnos = self.turnos_de_operarios(usuario_ids)
        return {usuario_id: resumen_turno(turnos.turno_de(usuario_id, hoy)) for usuario_id in usuario_ids}

    # ---------- Permisos y búsquedas ----------

    @staticmethod
    def _exigir_administrador(solicitante: dict) -> None:
        if solicitante["rol"] != Rol.ADMINISTRADOR.value:
            raise ProhibidoError("Solo el Administrador gestiona los turnos")

    def _turno_de_la_empresa(self, turno_id: str, solicitante: dict) -> Turno:
        doc = self.turno_repository.find_by_id(turno_id)
        if not doc or doc.get("empresa_id") != solicitante["empresa_id"]:
            raise NotFoundError("El turno no existe en tu empresa")
        return Turno.desde_documento(doc)

    def _operario_de_la_empresa(self, operario_id: str, solicitante: dict) -> dict:
        usuario = self.usuario_repository.find_by_id(operario_id)
        if not usuario or usuario.get("empresa_id") != solicitante["empresa_id"] \
                or usuario.get("rol") != Rol.OPERARIO.value:
            raise NotFoundError("El operario no existe en tu empresa")
        return usuario

    def _zona_de(self, empresa_id: str) -> str:
        empresa = self.empresa_repository.find_by_id(empresa_id) or {}
        return empresa.get("zona_horaria") or ZONA_POR_DEFECTO
