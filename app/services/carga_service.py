from collections import defaultdict

from app.models.enums import Rol
from app.utils.errors import ProhibidoError
from app.utils.fechas import validar_fecha

# Capacidad de una jornada en minutos (turno de 8 h menos 1 h de descanso).
# PROVISIONAL: cuando existan los turnos, la capacidad se calculará desde el turno de cada operario
# (alcance, Sección 5.2).
CAPACIDAD_JORNADA_MIN = 420


class CargaService:
    """Calcula la carga laboral: tiempo estimado de las actividades de cada operario por jornada."""

    def __init__(self, actividad_repository, asignacion_repository, usuario_repository):
        self.actividad_repository = actividad_repository
        self.asignacion_repository = asignacion_repository
        self.usuario_repository = usuario_repository

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
        return self.carga_por_jornada(solicitante["empresa_id"], fecha_desde, fecha_hasta, operario_ids)

    def carga_por_jornada(self, empresa_id: str, fecha_desde: str, fecha_hasta: str,
                          operario_ids: list = None) -> dict:
        operarios = self.usuario_repository.find_by_empresa_y_rol(empresa_id, Rol.OPERARIO.value)
        if operario_ids is not None:
            operarios = [o for o in operarios if str(o["_id"]) in operario_ids]
        ids = [str(o["_id"]) for o in operarios]

        asignaciones = self.asignacion_repository.find_by_usuarios(ids)
        actividades = self.actividad_repository.buscar(
            empresa_id, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
            ids=list({a["actividad_id"] for a in asignaciones}),
        )
        por_id = {str(a["_id"]): a for a in actividades}

        # El tiempo estimado se suma completo a cada operario asignado (no se divide entre ellos).
        minutos = defaultdict(lambda: defaultdict(int))
        for asignacion in asignaciones:
            actividad = por_id.get(asignacion["actividad_id"])
            if actividad:
                minutos[asignacion["usuario_id"]][actividad["fecha_programada"]] += \
                    actividad.get("tiempo_estimado_min") or 0

        return {
            "capacidad_min": CAPACIDAD_JORNADA_MIN,
            "operarios": [
                {
                    "id": str(operario["_id"]),
                    "nombre": operario["nombre"],
                    "jornadas": [self._jornada(fecha, total) for fecha, total in
                                 sorted(minutos[str(operario["_id"])].items())],
                }
                for operario in operarios
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
    def _jornada(fecha: str, minutos: int) -> dict:
        return {
            "fecha": fecha,
            "minutos": minutos,
            "porcentaje": round(minutos * 100 / CAPACIDAD_JORNADA_MIN),
            "sobrecarga": minutos > CAPACIDAD_JORNADA_MIN,
        }
