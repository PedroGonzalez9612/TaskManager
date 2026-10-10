"""Programación del día y orden del día de un operario (alcance, Sección 5.1).

Este servicio reúne los datos y hace cumplir quién puede ver o cambiar qué. El cálculo de la
programación está en programacion_dia.py (función pura) y el orden sugerido en OrdenJornada."""
from app.models.enums import EstadoActividad, Prioridad, Rol
from app.models.orden_jornada import OrdenJornada
from app.services.programacion_dia import programar_dia
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError
from app.utils.reloj import ZONA_POR_DEFECTO, ahora_utc, fecha_local

# Lo que el operario todavía tiene por hacer: es lo único que se puede ordenar.
ESTADOS_PENDIENTES = (EstadoActividad.ASIGNADA.value, EstadoActividad.PAUSADA.value)


def _motivo_para_no_ordenar(actividad):
    """Por qué esa actividad no puede entrar en el orden del día, o None si sí puede.
    "actividad" es None cuando el id no corresponde a una actividad del operario en esta jornada."""
    if actividad is None:
        return "Esa actividad no es tuya o no es de hoy"
    if actividad["estado"] not in ESTADOS_PENDIENTES:
        return "Solo se ordena lo que está pendiente"
    if actividad["prioridad"] == Prioridad.URGENTE.value:
        return "Las actividades urgentes no se reordenan"
    if actividad.get("hora_programada"):
        return "Solo se pueden ordenar las actividades de horario flexible"
    return None


def _turno_de_hoy(turno, fecha: str, zona: str) -> dict | None:
    """El turno del operario en la jornada, con su inicio y su fin como momentos UTC, o None."""
    if turno is None:
        return None
    return {
        "nombre": turno.nombre, "hora_inicio": turno.hora_inicio, "hora_fin": turno.hora_fin,
        "inicio": turno.inicio_en(fecha, zona), "fin": turno.fin_en(fecha, zona),
        "capacidad_min": turno.capacidad_min,
    }


def _validar_ids(actividad_ids) -> list:
    if not isinstance(actividad_ids, list) or not all(isinstance(i, str) and i for i in actividad_ids):
        raise ValidationError("actividad_ids debe ser una lista con los identificadores de las actividades")
    return actividad_ids


class ProgramacionService:
    """La programación del día se calcula cada vez que se consulta; solo se guarda el orden que el
    operario eligió para sus actividades de horario flexible. Ese orden vale para una jornada: al
    día siguiente se empieza otra vez con el sugerido."""

    def __init__(self, actividad_service, orden_jornada_repository, empresa_repository,
                 usuario_repository, turno_service, asistencia_service, reloj=None):
        self.actividad_service = actividad_service
        self.orden_jornada_repository = orden_jornada_repository
        self.empresa_repository = empresa_repository
        self.usuario_repository = usuario_repository
        # El turno da la capacidad y el horario de la jornada; la asistencia, las marcas del operario.
        self.turno_service = turno_service
        self.asistencia_service = asistencia_service
        # La hora la pone el servidor. Las pruebas pasan un reloj que ellas controlan.
        self.reloj = reloj or ahora_utc

    # ---------- Consultar (Administrador y Operario) ----------

    def consultar(self, solicitante: dict, operario_id=None) -> dict:
        """La programación de hoy. El Operario ve siempre la suya; el Administrador, la del operario
        de su empresa que indique."""
        operario = self._operario_consultado(solicitante, operario_id)
        return self._programacion(operario, self.reloj())

    # ---------- Orden del día (Operario) ----------

    def guardar_orden(self, solicitante: dict, actividad_ids) -> dict:
        """Guarda el orden que el operario eligió para hoy. Solo entran sus actividades pendientes
        de horario flexible que no sean urgentes. Una lista vacía equivale a restablecer el orden."""
        self._exigir_operario(solicitante)
        actividad_ids = _validar_ids(actividad_ids)
        ahora = self.reloj()
        fecha, zona, actividades = self._jornada(solicitante, ahora)

        por_id = {actividad["id"]: actividad for actividad in actividades}
        for actividad_id in actividad_ids:
            motivo = _motivo_para_no_ordenar(por_id.get(actividad_id))
            if motivo:
                raise ValidationError(motivo)

        orden = OrdenJornada(solicitante["id"], fecha, actividad_ids, fecha_actualizacion=ahora)
        if orden.es_personalizado:
            self.orden_jornada_repository.guardar(orden.to_dict())
        else:
            self.orden_jornada_repository.eliminar(solicitante["id"], fecha)
        return self._armar(solicitante, fecha, zona, actividades, ahora)

    def restablecer_orden(self, solicitante: dict) -> dict:
        """Quita el orden que el operario eligió para hoy: vuelve a valer el sugerido."""
        self._exigir_operario(solicitante)
        ahora = self.reloj()
        fecha, zona, actividades = self._jornada(solicitante, ahora)
        self.orden_jornada_repository.eliminar(solicitante["id"], fecha)
        return self._armar(solicitante, fecha, zona, actividades, ahora)

    # ---------- Permisos ----------

    @staticmethod
    def _exigir_operario(solicitante: dict) -> None:
        if solicitante["rol"] != Rol.OPERARIO.value:
            raise ProhibidoError("Solo el operario define su orden del día")

    def _operario_consultado(self, solicitante: dict, operario_id) -> dict:
        """El operario cuya programación se va a mostrar, con la forma de un solicitante: así
        ActividadService presenta las actividades con el estado personal de ese operario."""
        if solicitante["rol"] == Rol.OPERARIO.value:
            return solicitante
        if not operario_id:
            raise ValidationError("Indica el operario del que quieres ver la programación del día")
        usuario = self.usuario_repository.find_by_id(operario_id)
        if not usuario or usuario.get("empresa_id") != solicitante["empresa_id"] \
                or usuario.get("rol") != Rol.OPERARIO.value:
            raise NotFoundError("El operario no existe en tu empresa")
        return {
            "id": str(usuario["_id"]), "nombre": usuario["nombre"],
            "rol": Rol.OPERARIO.value, "empresa_id": usuario["empresa_id"],
        }

    # ---------- Armado de la programación ----------

    def _programacion(self, operario: dict, ahora) -> dict:
        fecha, zona, actividades = self._jornada(operario, ahora)
        return self._armar(operario, fecha, zona, actividades, ahora)

    def _jornada(self, operario: dict, ahora) -> tuple:
        """La fecha de hoy para la empresa, su zona horaria y las actividades del operario en esa
        jornada, presentadas con su estado personal (ActividadService cierra antes la jornada)."""
        empresa = self.empresa_repository.find_by_id(operario["empresa_id"]) or {}
        zona = empresa.get("zona_horaria") or ZONA_POR_DEFECTO
        fecha = fecha_local(ahora, zona)
        actividades = self.actividad_service.listar_actividades(
            {"fecha_desde": fecha, "fecha_hasta": fecha}, operario,
        )
        return fecha, zona, actividades

    def _armar(self, operario: dict, fecha: str, zona: str, actividades: list, ahora) -> dict:
        orden = self._orden_de(operario["id"], fecha)
        turnos = self.turno_service.turnos_de_operarios([operario["id"]])
        turno = turnos.turno_de(operario["id"], fecha)
        capacidad = turnos.capacidad_de(operario["id"], fecha)
        programacion = programar_dia(actividades, orden, ahora, fecha, zona, capacidad)
        turno_hoy = _turno_de_hoy(turno, fecha, zona)
        return {
            "fecha": fecha,
            "operario_id": operario["id"],
            "orden_personalizado": orden.es_personalizado,
            "tramos": programacion["tramos"],
            "resumen": programacion["resumen"],
            "actividades": actividades,
            "turno": turno_hoy,
            "asistencia": self.asistencia_service.actual(operario["id"], fecha, ahora),
            "en_turno": bool(turno_hoy) and turno_hoy["inicio"] <= ahora < turno_hoy["fin"],
        }

    def _orden_de(self, usuario_id: str, fecha: str) -> OrdenJornada:
        """El orden que el operario guardó para esa jornada; sin uno guardado, queda vacío y vale
        el sugerido. Se busca por fecha: el de otro día nunca se usa."""
        doc = self.orden_jornada_repository.find_de_usuario(usuario_id, fecha)
        return OrdenJornada.desde_documento(doc) if doc else OrdenJornada(usuario_id, fecha)
