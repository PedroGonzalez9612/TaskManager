"""La pantalla Hoy del Administrador (alcance, Sección 6.2): cómo va cada persona y lo que pide una
decisión suya. No tiene reglas propias: junta lo que ya calculan los demás servicios y le aplica las
reglas de presencia y de carga del modelo (app/models/presencia.py), las mismas de todo el sistema."""
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.models.asistencia import Asistencia
from app.models.enums import (
    MOTIVOS_DETENER_HORA_FIJA, EstadoActividad, EstadoCarga, EstadoEjecucion, EstadoPresencia, Rol,
)
from app.models.presencia import estado_de_carga, presencia_en_jornada
from app.services.turno_service import dia_anterior, resumen_turno
from app.utils.errors import ProhibidoError
from app.utils.reloj import ZONA_POR_DEFECTO, fecha_local


@dataclass
class _Persona:
    """Lo que se sabe de un operario hoy, antes de presentarlo."""
    id: str
    nombre: str
    jornada: str
    turno: object
    presencia: dict
    carga: dict
    actividad: dict
    pendientes_de_hoy: list = field(default_factory=list)    # Lo suyo de hoy que nadie ha iniciado.


def _es_final(actividad: dict) -> bool:
    return EstadoActividad(actividad["estado_general"]).es_final


def _ejecucion_de(actividad: dict, usuario_id: str):
    return next((e for e in actividad.get("ejecuciones", []) if e.get("usuario_id") == usuario_id), None)


def _detenida_por_emergencia(actividad: dict, ejecucion) -> bool:
    """Una de hora fija pausada con uno de los motivos de emergencia (alcance, Sección 5.1)."""
    if not actividad.get("hora_programada") or not ejecucion or ejecucion["estado"] != EstadoEjecucion.PAUSADA.value:
        return False
    pausas = ejecucion.get("pausas") or []
    return bool(pausas) and pausas[-1].get("motivo") in MOTIVOS_DETENER_HORA_FIJA


def _resumen_actividad(actividad: dict) -> dict:
    return {"id": actividad["id"], "codigo": actividad["codigo"], "titulo": actividad["titulo"],
            "tiempo_estimado_min": actividad["tiempo_estimado_min"], "hora_programada": actividad.get("hora_programada")}


def _actividad_de(usuario_id: str, actividades: list) -> dict:
    """Qué está haciendo: la que tiene en curso, una de hora fija detenida por emergencia, o nada."""
    for actividad in actividades:
        ejecucion = _ejecucion_de(actividad, usuario_id)
        if ejecucion and ejecucion["estado"] == EstadoEjecucion.EN_PROGRESO.value:
            return {"tipo": "EN_CURSO", **_resumen_actividad(actividad), "minutos": ejecucion["tiempo_real_min"]}
    for actividad in actividades:
        ejecucion = _ejecucion_de(actividad, usuario_id)
        if _detenida_por_emergencia(actividad, ejecucion):
            return {"tipo": "DETENIDA", **_resumen_actividad(actividad), "motivo": ejecucion["pausas"][-1]["motivo"],
                    "desde": ejecucion["pausas"][-1]["inicio"]}
    return {"tipo": "NINGUNA"}


class HoyService:
    def __init__(self, usuario_repository, empresa_repository, asistencia_repository, turno_service,
                 actividad_service, carga_service, reporte_service, reloj=None):
        self.reloj = reloj or (lambda: datetime.now(timezone.utc))
        self.usuario_repository = usuario_repository
        self.empresa_repository = empresa_repository
        self.asistencia_repository = asistencia_repository
        self.turno_service = turno_service
        self.actividad_service = actividad_service
        self.carga_service = carga_service
        self.reporte_service = reporte_service

    # ---------- Consultas ----------

    def personas(self, solicitante: dict) -> list:
        """Una fila por operario activo: su presencia, qué está haciendo y su carga de la jornada."""
        return [self._presentar(persona) for persona in self._personas(solicitante)]

    def pendientes(self, solicitante: dict) -> dict:
        """Solo lo que pide una decisión del Administrador, de lo más urgente a lo menos (alcance,
        Sección 6.2): quién llegó tarde (con lo suyo de hoy para reasignar), lo detenido por
        emergencia, lo que no tiene dueño, los reportes por revisar y quién está sobrecargado."""
        personas = self._personas(solicitante)
        llegada_tarde = [{**self._presentar(p), "actividades": p.pendientes_de_hoy}
                         for p in personas if p.presencia["estado"] == EstadoPresencia.LLEGADA_TARDE.value]
        detenidas = [self._presentar(p) for p in personas if p.actividad["tipo"] == "DETENIDA"]
        hoy = fecha_local(self.reloj(), self._zona_de(solicitante["empresa_id"]))
        sin_dueno = self.actividad_service.listar_actividades({"sin_asignar": True, "fecha_hasta": hoy}, solicitante)
        reportes = self.reporte_service.listar(solicitante, "PENDIENTE")
        sobrecargados = [self._presentar(p) for p in personas if p.carga["estado"] == EstadoCarga.SOBRECARGADO.value]
        grupos = {"llegada_tarde": llegada_tarde, "detenidas": detenidas, "sin_dueno": sin_dueno,
                  "reportes": reportes, "sobrecargados": sobrecargados}
        return {**grupos, "total": sum(len(grupo) for grupo in grupos.values())}

    # ---------- Armado ----------

    def _personas(self, solicitante: dict) -> list:
        if solicitante["rol"] != Rol.ADMINISTRADOR.value:
            raise ProhibidoError("Solo el Administrador ve el día de su equipo")
        empresa_id = solicitante["empresa_id"]
        ahora = self.reloj()
        zona = self._zona_de(empresa_id)
        hoy = fecha_local(ahora, zona)
        ayer = dia_anterior(hoy)     # Con un turno de noche, la jornada vigente puede ser la de ayer.

        operarios = self.usuario_repository.find_by_empresa_y_rol(empresa_id, Rol.OPERARIO.value)
        ids = [str(o["_id"]) for o in operarios]
        turnos = self.turno_service.turnos_de_operarios(ids)
        asistencias = {(a["usuario_id"], a["jornada"]): Asistencia.desde_documento(a)
                       for a in self.asistencia_repository.find_de_empresa_entre(empresa_id, ayer, hoy)}
        actividades = self.actividad_service.listar_actividades({"fecha_desde": ayer, "fecha_hasta": hoy}, solicitante)
        carga = {o["id"]: {j["fecha"]: j for j in o["jornadas"]}
                 for o in self.carga_service.carga_por_jornada(empresa_id, ayer, hoy, ids)["operarios"]}

        personas = []
        for operario, usuario_id in zip(operarios, ids):
            jornada = turnos.jornada_vigente(usuario_id, ahora, zona)
            turno = turnos.turno_de(usuario_id, jornada)
            presencia = presencia_en_jornada(turno.ventana_en(jornada, zona) if turno else None,
                                             asistencias.get((usuario_id, jornada)), ahora)
            suyas = [a for a in actividades if any(o["id"] == usuario_id for o in a["operarios"])]
            capacidad = turnos.capacidad_de(usuario_id, jornada)
            minutos = carga.get(usuario_id, {}).get(jornada, {}).get("minutos", 0)
            personas.append(_Persona(
                id=usuario_id, nombre=operario["nombre"], jornada=jornada, turno=turno,
                presencia={"estado": presencia["estado"].value, "minutos": presencia["minutos"]},
                carga={"minutos": minutos, "capacidad_min": capacidad, "porcentaje": round(minutos * 100 / capacidad) if capacidad else 0,
                       "estado": estado_de_carga(minutos, capacidad).value},
                actividad=_actividad_de(usuario_id, suyas),
                pendientes_de_hoy=[a for a in suyas if a["fecha_programada"] == jornada and not _es_final(a)
                                   and _ejecucion_de(a, usuario_id) is None],
            ))
        return personas

    @staticmethod
    def _presentar(persona: _Persona) -> dict:
        return {"id": persona.id, "nombre": persona.nombre, "jornada": persona.jornada,
                "turno": resumen_turno(persona.turno), "presencia": persona.presencia,
                "actividad": persona.actividad, "carga": persona.carga}

    def _zona_de(self, empresa_id: str) -> str:
        empresa = self.empresa_repository.find_by_id(empresa_id) or {}
        return empresa.get("zona_horaria") or ZONA_POR_DEFECTO
