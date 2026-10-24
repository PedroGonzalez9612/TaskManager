"""Indicadores de jornada y cumplimiento (alcance, Sección 5.2; criterio 8 del MVP).

Por cada jornada de cada operario: tiempo programado (su capacidad), tiempo presente (asistencia
validada o corregida), tiempo en actividades (ejecución sin pausas) y tiempo adicional (trabajo fuera
de su turno). Por cada asignación: si la actividad se cumplió en su jornada. Y los pendientes:
reprogramadas, no realizadas, canceladas y devoluciones por motivo.

Regla de los agregados: se suman los tiempos y los conteos de todos los involucrados y se divide al
final; nunca se promedian porcentajes. Los porcentajes son None cuando no hay con qué dividir.

Supuestos (anotados en docs/casos_por_definir.md):
- Una jornada cuenta si el operario marcó asistencia o tenía actividades ese día: el turno no tiene
  días de descanso, y sin esto los domingos bajarían el cumplimiento.
- Solo cuentan las jornadas que ya terminaron (las anteriores a hoy) y la de hoy si ya marcó la salida.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from app.models.ejecucion import minutos_trabajados_en
from app.models.enums import EstadoActividad, EstadoAsignacion, EstadoEjecucion, Rol
from app.models.asistencia import EstadoAsistencia
from app.models.pausa import en_utc
from app.utils.errors import ProhibidoError, ValidationError
from app.utils.fechas import validar_fecha
from app.utils.reloj import ZONA_POR_DEFECTO, fecha_local, momento_local

DIAS_MAXIMOS = 92                   # Un trimestre: la consulta recorre cada día de cada operario.
ASISTENCIA_REVISADA = (EstadoAsistencia.VALIDADA.value, EstadoAsistencia.CORREGIDA.value)


def _porcentaje(parte, total):
    return round(parte * 100 / total) if total else None


def _dias(desde: str, hasta: str) -> list:
    inicio, fin = date.fromisoformat(desde), date.fromisoformat(hasta)
    return [(inicio + timedelta(days=dia)).isoformat() for dia in range((fin - inicio).days + 1)]


def _pausas(ejecucion: dict) -> list:
    return [(pausa["inicio"], pausa.get("fin")) for pausa in ejecucion.get("pausas") or []]


# ---------- Acumuladores: se suman y al final se divide ----------

@dataclass
class TiemposDeJornada:
    jornadas: int = 0
    programado_min: int = 0
    presente_min: int = 0
    actividades_min: int = 0
    actividades_con_presencia_min: int = 0     # Solo de las jornadas con asistencia revisada.
    adicional_min: int = 0
    sin_validar: int = 0                        # Jornadas con marcas que el Administrador no ha revisado.

    def sumar(self, otro: "TiemposDeJornada") -> None:
        for campo in self.__dataclass_fields__:
            setattr(self, campo, getattr(self, campo) + getattr(otro, campo))

    def presentar(self) -> dict:
        return {
            "jornadas": self.jornadas,
            "programado_min": self.programado_min,
            "presente_min": self.presente_min,
            "actividades_min": self.actividades_min,
            "adicional_min": self.adicional_min,
            "jornadas_sin_validar": self.sin_validar,
            "cumplimiento_jornada": _porcentaje(self.actividades_min, self.programado_min),
            "aprovechamiento": _porcentaje(self.actividades_con_presencia_min, self.presente_min),
        }


@dataclass
class CumplimientoDeActividades:
    cumplidas: int = 0
    incumplidas: int = 0                # No realizadas.
    con_retraso: int = 0                # Reprogramadas, o finalizadas después de su jornada.
    pendientes: int = 0                 # Su jornada no ha terminado: todavía no cuentan.
    estimado_min: int = 0               # De las finalizadas: el estimado, una vez por operario.
    real_min: int = 0                   # De las finalizadas: el tiempo real, sin pausas.

    def sumar(self, otro: "CumplimientoDeActividades") -> None:
        for campo in self.__dataclass_fields__:
            setattr(self, campo, getattr(self, campo) + getattr(otro, campo))

    def presentar(self) -> dict:
        evaluadas = self.cumplidas + self.incumplidas + self.con_retraso
        return {
            "cumplidas": self.cumplidas,
            "incumplidas": self.incumplidas,
            "con_retraso": self.con_retraso,
            "pendientes": self.pendientes,
            "cumplimiento_actividades": _porcentaje(self.cumplidas, evaluadas),
            "estimado_min": self.estimado_min,
            "real_min": self.real_min,
            # Precisión de estimación: el tiempo real como porcentaje del estimado (100 = exacto).
            "real_sobre_estimado": _porcentaje(self.real_min, self.estimado_min),
        }


@dataclass
class Pendientes:
    reprogramadas: int = 0
    dias_de_retraso: list = field(default_factory=list)
    no_realizadas: int = 0
    canceladas: Counter = field(default_factory=Counter)
    devoluciones: Counter = field(default_factory=Counter)

    def presentar(self) -> dict:
        def por_motivo(conteo):
            return [{"motivo": motivo, "cantidad": cantidad} for motivo, cantidad in conteo.most_common()]
        return {
            "reprogramadas": self.reprogramadas,
            "dias_de_retraso_maximo": max(self.dias_de_retraso, default=0),
            "no_realizadas": self.no_realizadas,
            "canceladas": sum(self.canceladas.values()),
            "canceladas_por_motivo": por_motivo(self.canceladas),
            "devoluciones": sum(self.devoluciones.values()),
            "devoluciones_por_motivo": por_motivo(self.devoluciones),
        }


# ---------- Cálculos puros ----------

def tiempos_de_jornada(capacidad_min: int, ventana: tuple, turno_ventana, asistencia,
                       ejecuciones: list, ahora) -> TiemposDeJornada:
    """Los tiempos de un operario en una jornada. "ventana" es (desde, hasta) de la jornada;
    "turno_ventana", (inicio, fin) de su turno o None; "asistencia", su documento o None."""
    tiempos = TiemposDeJornada(jornadas=1, programado_min=capacidad_min)
    for ejecucion in ejecuciones:
        if not ejecucion.get("fecha_inicio"):
            continue
        fin = ejecucion.get("fecha_fin") or ahora
        en_jornada = minutos_trabajados_en(ejecucion["fecha_inicio"], fin, _pausas(ejecucion), *ventana)
        tiempos.actividades_min += en_jornada
        if turno_ventana:
            dentro = minutos_trabajados_en(ejecucion["fecha_inicio"], fin, _pausas(ejecucion), *turno_ventana)
            tiempos.adicional_min += max(0, en_jornada - dentro)
    if asistencia and asistencia.get("salida") and asistencia.get("estado") in ASISTENCIA_REVISADA:
        tiempos.presente_min = round((en_utc(asistencia["salida"]) - en_utc(asistencia["entrada"])).total_seconds() / 60)
        tiempos.actividades_con_presencia_min = tiempos.actividades_min
    elif asistencia:
        tiempos.sin_validar = 1
    return tiempos


def cumplimiento_de_asignacion(actividad: dict, ejecucion, cierre_de_su_jornada, ahora) -> CumplimientoDeActividades:
    """Cómo terminó una asignación (alcance, Sección 5.2): cumplida si el operario la finalizó en su
    jornada programada; incumplida si quedó No realizada; con retraso si se reprogramó o se finalizó
    después. Las canceladas no se evalúan (las excluye quien llama)."""
    resultado = CumplimientoDeActividades()
    estado = actividad.get("estado")
    finalizada = ejecucion and ejecucion.get("estado") == EstadoEjecucion.FINALIZADA.value
    if finalizada:
        resultado.estimado_min = actividad.get("tiempo_estimado_min") or 0
        resultado.real_min = minutos_trabajados_en(
            ejecucion["fecha_inicio"], ejecucion["fecha_fin"], _pausas(ejecucion),
            en_utc(ejecucion["fecha_inicio"]), en_utc(ejecucion["fecha_fin"]))
    if estado == EstadoActividad.NO_REALIZADA.value:
        resultado.incumplidas = 1
    elif actividad.get("reprogramaciones"):
        resultado.con_retraso = 1
    elif finalizada:
        a_tiempo = en_utc(ejecucion["fecha_fin"]) <= cierre_de_su_jornada
        resultado.cumplidas, resultado.con_retraso = (1, 0) if a_tiempo else (0, 1)
    elif en_utc(ahora) < cierre_de_su_jornada:
        resultado.pendientes = 1
    else:
        # Su jornada terminó y no se finalizó ni se reprogramó (por ejemplo, sigue pausada).
        resultado.con_retraso = 1
    return resultado


# ---------- El servicio ----------

class IndicadorService:
    def __init__(self, actividad_repository, asignacion_repository, ejecucion_repository, asistencia_repository,
                 usuario_repository, empresa_repository, proyecto_repository, turno_service, cierre_jornada,
                 reloj=None):
        self.actividad_repository = actividad_repository
        self.asignacion_repository = asignacion_repository
        self.ejecucion_repository = ejecucion_repository
        self.asistencia_repository = asistencia_repository
        self.usuario_repository = usuario_repository
        self.empresa_repository = empresa_repository
        self.proyecto_repository = proyecto_repository
        self.turno_service = turno_service
        self.cierre_jornada = cierre_jornada
        # La hora la pone el servidor. Las pruebas pasan un reloj que ellas controlan.
        self.reloj = reloj or (lambda: datetime.now(timezone.utc))

    def consultar(self, desde, hasta, solicitante: dict) -> dict:
        """Indicadores entre dos jornadas. El Administrador ve su empresa completa, por operario, por
        proyecto y por categoría; el Operario, solo los suyos."""
        desde = validar_fecha(desde, "La fecha inicial")
        hasta = validar_fecha(hasta, "La fecha final")
        if hasta < desde:
            raise ValidationError("La fecha final no puede ser anterior a la inicial")
        if (date.fromisoformat(hasta) - date.fromisoformat(desde)).days >= DIAS_MAXIMOS:
            raise ValidationError(f"Consulta como máximo {DIAS_MAXIMOS} días")
        if solicitante["rol"] not in (Rol.ADMINISTRADOR.value, Rol.OPERARIO.value):
            raise ProhibidoError("No tienes acceso a los indicadores")

        empresa_id = solicitante["empresa_id"]
        # Antes de medir: lo atrasado pasa a su nueva jornada y lo vencido queda No realizado.
        self.cierre_jornada.cerrar_pendientes(empresa_id)
        ahora = self.reloj()
        zona = (self.empresa_repository.find_by_id(empresa_id) or {}).get("zona_horaria") or ZONA_POR_DEFECTO

        operarios = self.usuario_repository.find_by_empresa_y_rol(empresa_id, Rol.OPERARIO.value)
        if solicitante["rol"] == Rol.OPERARIO.value:
            operarios = [o for o in operarios if str(o["_id"]) == solicitante["id"]]
        ids = [str(o["_id"]) for o in operarios]
        turnos = self.turno_service.turnos_de_operarios(ids)

        actividades = {str(a["_id"]): a for a in self.actividad_repository.buscar_por_jornada_original(empresa_id, desde, hasta)}
        asignaciones = [a for a in self.asignacion_repository.find_by_actividades(list(actividades), incluir_historial=True)
                        if a["usuario_id"] in ids]
        ejecucion_de = {e.get("asignacion_id"): e for e in self.ejecucion_repository.find_by_actividades(list(actividades))}

        jornada = self._jornadas(ids, desde, hasta, turnos, zona, asignaciones, actividades, ahora, empresa_id)
        actividades_por = self._actividades(asignaciones, actividades, ejecucion_de, turnos, zona, ahora)
        pendientes = self._pendientes(asignaciones, actividades)

        nombres = {str(o["_id"]): o["nombre"] for o in operarios}
        proyectos = {str(p["_id"]): p["nombre"] for p in self.proyecto_repository.find_by_empresa(empresa_id)}
        empresa_jornada, empresa_actividades = TiemposDeJornada(), CumplimientoDeActividades()
        for tiempos in jornada.values():
            empresa_jornada.sumar(tiempos)
        for cumplimiento in actividades_por["operario"].values():
            empresa_actividades.sumar(cumplimiento)

        return {
            "desde": desde,
            "hasta": hasta,
            "empresa": {"jornada": empresa_jornada.presentar(), "actividades": empresa_actividades.presentar(),
                        "pendientes": pendientes["empresa"].presentar()},
            "operarios": [
                {"id": usuario_id, "nombre": nombres[usuario_id],
                 "jornada": jornada[usuario_id].presentar(),
                 "actividades": actividades_por["operario"][usuario_id].presentar(),
                 "pendientes": pendientes["operario"][usuario_id].presentar()}
                for usuario_id in ids
            ],
            "categorias": [
                {"categoria": categoria, "actividades": valor.presentar()}
                for categoria, valor in sorted(actividades_por["categoria"].items())
            ],
            "proyectos": [
                {"id": proyecto_id, "nombre": proyectos.get(proyecto_id, "Proyecto"), "actividades": valor.presentar()}
                for proyecto_id, valor in actividades_por["proyecto"].items() if proyecto_id
            ],
        }

    # ---------- Jornadas: tiempos de cada operario ----------

    def _jornadas(self, ids, desde, hasta, turnos, zona, asignaciones, actividades, ahora, empresa_id) -> dict:
        hoy = fecha_local(ahora, zona)
        asistencias = {(a["usuario_id"], a["jornada"]): a
                       for a in self.asistencia_repository.find_de_empresa_entre(empresa_id, desde, hasta)}
        # Días en que cada operario tenía actividades: también son jornadas aunque no haya marcado.
        con_actividades = defaultdict(set)
        for asignacion in asignaciones:
            actividad = actividades[asignacion["actividad_id"]]
            if actividad.get("estado") != EstadoActividad.CANCELADA.value:
                con_actividades[asignacion["usuario_id"]].add(actividad.get("fecha_original") or actividad["fecha_programada"])

        inicio_rango = momento_local(desde, "00:00", zona)
        fin_rango = turnos.cierre_de(ids, hasta, zona) if ids else momento_local(hasta, "23:59", zona)
        ejecuciones = defaultdict(list)
        for ejecucion in self.ejecucion_repository.find_de_usuarios_entre(ids, inicio_rango, fin_rango):
            ejecuciones[ejecucion["usuario_id"]].append(ejecucion)

        resultado = {}
        for usuario_id in ids:
            total = TiemposDeJornada()
            for fecha in _dias(desde, hasta):
                asistencia = asistencias.get((usuario_id, fecha))
                if fecha > hoy or (fecha == hoy and not (asistencia and asistencia.get("salida"))):
                    continue
                if not asistencia and fecha not in con_actividades[usuario_id]:
                    continue
                turno = turnos.turno_de(usuario_id, fecha)
                ventana = (momento_local(fecha, "00:00", zona), turnos.cierre_de([usuario_id], fecha, zona))
                turno_ventana = (turno.inicio_en(fecha, zona), turno.fin_en(fecha, zona)) if turno else None
                total.sumar(tiempos_de_jornada(turnos.capacidad_de(usuario_id, fecha), ventana, turno_ventana,
                                               asistencia, ejecuciones[usuario_id], ahora))
            resultado[usuario_id] = total
        return resultado

    # ---------- Actividades: cumplimiento por operario, categoría y proyecto ----------

    @staticmethod
    def _actividades(asignaciones, actividades, ejecucion_de, turnos, zona, ahora) -> dict:
        por = {"operario": defaultdict(CumplimientoDeActividades), "categoria": defaultdict(CumplimientoDeActividades),
               "proyecto": defaultdict(CumplimientoDeActividades)}
        for asignacion in asignaciones:
            actividad = actividades[asignacion["actividad_id"]]
            # Lo devuelto o retirado ya no es del operario; lo cancelado no se evalúa (alcance, Sección 5.2).
            if asignacion.get("estado") != EstadoAsignacion.ACTIVA.value \
                    or actividad.get("estado") == EstadoActividad.CANCELADA.value:
                continue
            jornada = actividad.get("fecha_original") or actividad["fecha_programada"]
            cierre = turnos.cierre_de([asignacion["usuario_id"]], jornada, zona)
            resultado = cumplimiento_de_asignacion(actividad, ejecucion_de.get(str(asignacion["_id"])), cierre, ahora)
            por["operario"][asignacion["usuario_id"]].sumar(resultado)
            por["categoria"][actividad.get("categoria")].sumar(resultado)
            por["proyecto"][actividad.get("proyecto_id")].sumar(resultado)
        return por

    # ---------- Pendientes, cancelaciones y devoluciones ----------

    @staticmethod
    def _pendientes(asignaciones, actividades) -> dict:
        empresa = Pendientes()
        por_operario = defaultdict(Pendientes)
        for actividad_id, actividad in actividades.items():
            operarios = {a["usuario_id"] for a in asignaciones
                         if a["actividad_id"] == actividad_id and a.get("estado") == EstadoAsignacion.ACTIVA.value}
            destinos = [empresa, *(por_operario[usuario_id] for usuario_id in operarios)]
            estado = actividad.get("estado")
            if estado == EstadoActividad.CANCELADA.value:
                motivo = (actividad.get("cancelacion") or {}).get("motivo") or "Sin motivo"
                for destino in destinos:
                    destino.canceladas[motivo] += 1
            elif estado == EstadoActividad.NO_REALIZADA.value:
                for destino in destinos:
                    destino.no_realizadas += 1
            elif actividad.get("reprogramaciones") and not EstadoActividad(estado).es_final:
                dias = (date.fromisoformat(actividad["fecha_programada"])
                        - date.fromisoformat(actividad.get("fecha_original") or actividad["fecha_programada"])).days
                for destino in destinos:
                    destino.reprogramadas += 1
                    destino.dias_de_retraso.append(dias)
        for asignacion in asignaciones:
            if asignacion.get("estado") == EstadoAsignacion.DEVUELTA.value:
                motivo = (asignacion.get("devolucion") or {}).get("motivo") or "Sin motivo"
                empresa.devoluciones[motivo] += 1
                por_operario[asignacion["usuario_id"]].devoluciones[motivo] += 1
        return {"empresa": empresa, "operario": por_operario}
