from collections import defaultdict
from datetime import date, timedelta

from app.models.enums import EstadoActividad, Rol
from app.utils.errors import ProhibidoError
from app.utils.fechas import validar_fecha

# Las canceladas no suman a la carga; las no realizadas sí, porque ocuparon su lugar en el día
# (alcance, Sección 5.2).
ESTADOS_QUE_SUMAN = [estado.value for estado in EstadoActividad if estado != EstadoActividad.CANCELADA]

# Días como máximo para los que se informa el turno de cada operario (el tablero pide uno; Semana, siete).
DIAS_MAXIMOS_CON_TURNO = 31


def _dias(fecha_desde: str, fecha_hasta: str) -> list:
    desde, hasta = date.fromisoformat(fecha_desde), date.fromisoformat(fecha_hasta)
    cantidad = min((hasta - desde).days + 1, DIAS_MAXIMOS_CON_TURNO)
    return [(desde + timedelta(days=dia)).isoformat() for dia in range(max(0, cantidad))]


def _resumen_turno(turno) -> dict | None:
    """El horario del turno de ese día, o None si el operario no tiene turno."""
    if turno is None:
        return None
    return {"nombre": turno.nombre, "hora_inicio": turno.hora_inicio, "hora_fin": turno.hora_fin}


# Capacidad provisional de una jornada en minutos (turno de 8 h menos 1 h de descanso). Se usa para
# los operarios que todavía no tienen turno; con turno, la capacidad es la de su turno vigente en
# esa jornada (alcance, Sección 5.2; TurnoService.capacidad_de).
CAPACIDAD_JORNADA_MIN = 420


class CargaService:
    """Calcula la carga laboral: tiempo estimado de las actividades de cada operario por jornada."""

    def __init__(self, actividad_repository, asignacion_repository, usuario_repository, cierre_jornada,
                 turno_service):
        self.actividad_repository = actividad_repository
        self.asignacion_repository = asignacion_repository
        self.usuario_repository = usuario_repository
        self.cierre_jornada = cierre_jornada
        # La capacidad de cada operario en cada jornada sale de su turno vigente.
        self.turno_service = turno_service

    def consultar(self, fecha_desde: str, fecha_hasta: str, solicitante: dict) -> dict:
        """Carga por jornada. El Administrador ve a todos los operarios de su empresa; el Operario, solo la suya."""
        fecha_desde = validar_fecha(fecha_desde, "La fecha inicial")
        fecha_hasta = validar_fecha(fecha_hasta, "La fecha final")

        if solicitante["rol"] == Rol.ADMINISTRADOR.value:
            operario_ids = None
        elif solicitante["rol"] == Rol.OPERARIO.value:
            operario_ids = [solicitante["id"]]
        else:
            raise ProhibidoError("No tienes acceso a la carga laboral")
        # Antes de sumar: lo atrasado pasa a su nueva jornada (alcance, Sección 5.1).
        self.cierre_jornada.cerrar_pendientes(solicitante["empresa_id"])
        return self.carga_por_jornada(solicitante["empresa_id"], fecha_desde, fecha_hasta, operario_ids)

    def carga_por_jornada(self, empresa_id: str, fecha_desde: str, fecha_hasta: str,
                          operario_ids: list = None) -> dict:
        operarios = self.usuario_repository.find_by_empresa_y_rol(empresa_id, Rol.OPERARIO.value)
        if operario_ids is not None:
            operarios = [o for o in operarios if str(o["_id"]) in operario_ids]
        ids = [str(o["_id"]) for o in operarios]

        # Solo las asignaciones activas: al operario retirado o que devolvió la actividad ya no le suma.
        asignaciones = self.asignacion_repository.find_by_usuarios(ids)
        actividades = self.actividad_repository.buscar(
            empresa_id, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
            ids=list({a["actividad_id"] for a in asignaciones}),
            estados=ESTADOS_QUE_SUMAN,
        )
        por_id = {str(a["_id"]): a for a in actividades}

        # El tiempo estimado se suma completo a cada operario asignado (no se divide entre ellos).
        minutos = defaultdict(lambda: defaultdict(int))
        for asignacion in asignaciones:
            actividad = por_id.get(asignacion["actividad_id"])
            if actividad:
                minutos[asignacion["usuario_id"]][actividad["fecha_programada"]] += \
                    actividad.get("tiempo_estimado_min") or 0

        turnos = self.turno_service.turnos_de_operarios(ids)
        return {
            # La provisional, para compatibilidad: la de cada operario va en cada jornada.
            "capacidad_min": CAPACIDAD_JORNADA_MIN,
            "operarios": [
                {
                    "id": usuario_id,
                    "nombre": operario["nombre"],
                    "jornadas": [self._jornada(fecha, total, turnos.capacidad_de(usuario_id, fecha))
                                 for fecha, total in sorted(minutos[usuario_id].items())],
                    # El turno de cada día del rango: un cambio de turno rige desde su fecha.
                    "turnos": {fecha: _resumen_turno(turnos.turno_de(usuario_id, fecha))
                               for fecha in _dias(fecha_desde, fecha_hasta)},
                }
                for operario, usuario_id in zip(operarios, ids)
            ],
        }

    def sobrecargas(self, empresa_id: str, fecha: str, operario_ids: list) -> list:
        """Operarios cuya carga en esa jornada supera el 100 % de su capacidad (alerta del alcance)."""
        if not operario_ids:
            return []
        carga = self.carga_por_jornada(empresa_id, fecha, fecha, operario_ids)
        return [
            {"operario": operario["nombre"], **jornada}
            for operario in carga["operarios"]
            for jornada in operario["jornadas"]
            if jornada["sobrecarga"]
        ]

    @staticmethod
    def _jornada(fecha: str, minutos: int, capacidad_min: int) -> dict:
        """La carga de un operario en una jornada, comparada con su capacidad de esa jornada."""
        return {
            "fecha": fecha,
            "minutos": minutos,
            "capacidad_min": capacidad_min,
            "porcentaje": round(minutos * 100 / capacidad_min),
            "sobrecarga": minutos > capacidad_min,
        }
