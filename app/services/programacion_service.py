"""Programación del día y orden del día de un operario (alcance, Sección 5.1).

Este servicio reúne los datos y hace cumplir quién puede ver o cambiar qué. El cálculo de la
programación está en programacion_dia.py (función pura) y el orden sugerido en OrdenJornada.

La jornada que se programa es la jornada vigente del operario: con un turno de noche, después de
la medianoche sigue viendo la jornada del día en que empezó su turno, hasta que el turno termina."""
from dataclasses import dataclass
from datetime import date, timedelta

from app.models.enums import EstadoActividad, Prioridad, Rol
from app.models.orden_jornada import OrdenJornada
from app.services.programacion_dia import programar_dia
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError
from app.utils.fechas import validar_fecha
from app.utils.reloj import ZONA_POR_DEFECTO, ahora_utc, momento_local

# Lo que el operario todavía tiene por hacer: es lo único que se puede ordenar.
ESTADOS_PENDIENTES = (EstadoActividad.ASIGNADA.value, EstadoActividad.PAUSADA.value)

# Minutos después del inicio del turno a partir de los cuales una entrada sin marcar es una llegada
# tarde (alcance, Sección 5.1). Es la misma para todas las empresas mientras no se defina por empresa.
TOLERANCIA_ENTRADA_MIN = 10
# Días como máximo de una consulta de varios días (Semana pide siete).
DIAS_MAXIMOS_SEMANA = 14
# Un día futuro sin turno se proyecta desde esta hora: no hay inicio de turno del que partir.
HORA_SIN_TURNO = "08:00"
# Lo que todavía ocupa tiempo del operario: lo que está en curso y lo pendiente.
TRAMOS_CON_TIEMPO_POR_DELANTE = ("EN_CURSO", "PENDIENTE")


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


def _minutos_fuera_del_turno(tramo: dict, fin_turno) -> int:
    """Cuántos minutos del tramo caen después del fin del turno: el tiempo que el operario tendría
    que quedarse para hacerlo. Lo ya terminado no cuenta."""
    if fin_turno is None or tramo["tipo"] not in TRAMOS_CON_TIEMPO_POR_DELANTE or tramo["fin"] <= fin_turno:
        return 0
    return round((tramo["fin"] - max(tramo["inicio"], fin_turno)).total_seconds() / 60)


def _minutos_de_retraso(turno_hoy, asistencia, fecha: str, ahora) -> int:
    """Minutos que lleva el turno empezado sin la entrada marcada, si ya pasó la tolerancia; si no, 0.
    Una asistencia de otra jornada (que quedó sin salida) no cuenta como entrada de hoy."""
    if not turno_hoy or (asistencia and asistencia.get("jornada") == fecha):
        return 0
    if not turno_hoy["inicio"] <= ahora < turno_hoy["fin"]:
        return 0
    minutos = int((ahora - turno_hoy["inicio"]).total_seconds() // 60)
    return minutos if minutos > TOLERANCIA_ENTRADA_MIN else 0


def _validar_ids(actividad_ids) -> list:
    if not isinstance(actividad_ids, list) or not all(isinstance(i, str) and i for i in actividad_ids):
        raise ValidationError("actividad_ids debe ser una lista con los identificadores de las actividades")
    return actividad_ids


@dataclass
class _Jornada:
    """Lo que se necesita para programar la jornada vigente de un operario: su fecha, la zona
    horaria de la empresa, sus actividades de esa jornada y sus turnos (leídos una sola vez)."""
    fecha: str
    zona: str
    actividades: list
    turnos: object


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
        """La programación de la jornada vigente del operario. El Operario ve siempre la suya; el
        Administrador, la del operario de su empresa que indique."""
        operario = self._operario_consultado(solicitante, operario_id)
        return self._programacion(operario, self.reloj())

    def semana(self, solicitante: dict, desde, hasta, operario_id=None) -> dict:
        """La programación de varios días (vista Semana; observaciones 8 y 11 del usuario). Cada día
        con las mismas reglas de Hoy: lo pasado, con lo finalizado en sus horas reales; la jornada
        vigente, con su programación dinámica; lo futuro, proyectado desde el inicio de su turno, en
        el orden que el operario haya elegido. La hora fija nunca se mueve."""
        desde = validar_fecha(desde, "La fecha inicial")
        hasta = validar_fecha(hasta, "La fecha final")
        if hasta < desde:
            raise ValidationError("La fecha final no puede ser anterior a la inicial")
        dias = (date.fromisoformat(hasta) - date.fromisoformat(desde)).days + 1
        if dias > DIAS_MAXIMOS_SEMANA:
            raise ValidationError(f"Consulta como máximo {DIAS_MAXIMOS_SEMANA} días")

        operario = self._operario_consultado(solicitante, operario_id)
        ahora = self.reloj()
        empresa = self.empresa_repository.find_by_id(operario["empresa_id"]) or {}
        zona = empresa.get("zona_horaria") or ZONA_POR_DEFECTO
        turnos = self.turno_service.turnos_de_operarios([operario["id"]])
        vigente = turnos.jornada_vigente(operario["id"], ahora, zona)
        actividades = self.actividad_service.listar_actividades({"fecha_desde": desde, "fecha_hasta": hasta}, operario)
        por_fecha = {}
        for actividad in actividades:
            por_fecha.setdefault(actividad["fecha_programada"], []).append(actividad)

        resultado = []
        for indice in range(dias):
            fecha = (date.fromisoformat(desde) + timedelta(days=indice)).isoformat()
            del_dia = por_fecha.get(fecha, [])
            if fecha == vigente:
                dia = self._armar(operario, _Jornada(fecha, zona, del_dia, turnos), ahora)
            else:
                dia = self._otro_dia(operario, fecha, zona, del_dia, turnos, ahora, pasado=fecha < vigente)
            resultado.append({
                "fecha": fecha, "es_vigente": fecha == vigente, "turno": dia["turno"],
                "tramos": dia["tramos"], "resumen": dia["resumen"],
                "actividad_ids": [actividad["id"] for actividad in del_dia],
                # Solo la jornada vigente tiene asistencia: sin la entrada, el detalle no ofrece iniciar.
                "asistencia": dia.get("asistencia"),
            })
        return {"desde": desde, "hasta": hasta, "jornada_vigente": vigente, "dias": resultado,
                "actividades": actividades}

    def _otro_dia(self, operario: dict, fecha: str, zona: str, actividades: list, turnos, ahora, pasado: bool) -> dict:
        """La programación de un día que no es la jornada vigente. En uno pasado solo queda lo
        finalizado, en sus horas reales (lo que no se hizo ya pasó a otra jornada o quedó No
        realizado). En uno futuro, lo pendiente se proyecta desde el inicio de su turno."""
        turno = _turno_de_hoy(turnos.turno_de(operario["id"], fecha), fecha, zona)
        inicio = turno["inicio"] if turno else momento_local(fecha, HORA_SIN_TURNO, zona)
        programacion = programar_dia(actividades, self._orden_de(operario["id"], fecha), ahora, fecha, zona,
                                     turnos.capacidad_de(operario["id"], fecha),
                                     turnos.cierre_de([operario["id"]], fecha, zona), inicio_turno=inicio)
        tramos = programacion["tramos"]
        if pasado:
            tramos = [tramo for tramo in tramos if tramo["tipo"] == "FINALIZADA"]
        fin_turno = turno["fin"] if turno else None
        for tramo in tramos:
            tramo["fuera_del_turno_min"] = _minutos_fuera_del_turno(tramo, fin_turno)
        programacion["resumen"]["fuera_del_turno_min"] = sum(tramo["fuera_del_turno_min"] for tramo in tramos)
        return {"turno": turno, "tramos": tramos, "resumen": programacion["resumen"]}

    # ---------- Orden del día (Operario) ----------

    def guardar_orden(self, solicitante: dict, actividad_ids) -> dict:
        """Guarda el orden que el operario eligió para hoy. Solo entran sus actividades pendientes
        de horario flexible que no sean urgentes. Una lista vacía equivale a restablecer el orden."""
        self._exigir_operario(solicitante)
        actividad_ids = _validar_ids(actividad_ids)
        ahora = self.reloj()
        jornada = self._jornada(solicitante, ahora)
        self._validar_orden(jornada, actividad_ids)

        orden = OrdenJornada(solicitante["id"], jornada.fecha, actividad_ids, fecha_actualizacion=ahora)
        if orden.es_personalizado:
            self.orden_jornada_repository.guardar(orden.to_dict())
        else:
            self.orden_jornada_repository.eliminar(solicitante["id"], jornada.fecha)
        return self._armar(solicitante, jornada, ahora)

    def vista_previa_orden(self, solicitante: dict, actividad_ids) -> dict:
        """La programación como quedaría con ese orden, sin guardarlo: mientras el operario ordena su
        día, cada actividad muestra la hora en que quedaría (alcance, Sección 5.1). Las mismas reglas
        que al guardar."""
        self._exigir_operario(solicitante)
        actividad_ids = _validar_ids(actividad_ids)
        ahora = self.reloj()
        jornada = self._jornada(solicitante, ahora)
        self._validar_orden(jornada, actividad_ids)
        orden = OrdenJornada(solicitante["id"], jornada.fecha, actividad_ids, fecha_actualizacion=ahora)
        return self._armar(solicitante, jornada, ahora, orden)

    @staticmethod
    def _validar_orden(jornada, actividad_ids: list) -> None:
        por_id = {actividad["id"]: actividad for actividad in jornada.actividades}
        for actividad_id in actividad_ids:
            motivo = _motivo_para_no_ordenar(por_id.get(actividad_id))
            if motivo:
                raise ValidationError(motivo)

    def restablecer_orden(self, solicitante: dict) -> dict:
        """Quita el orden que el operario eligió para su jornada vigente: vuelve a valer el sugerido."""
        self._exigir_operario(solicitante)
        ahora = self.reloj()
        jornada = self._jornada(solicitante, ahora)
        self.orden_jornada_repository.eliminar(solicitante["id"], jornada.fecha)
        return self._armar(solicitante, jornada, ahora)

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
        return self._armar(operario, self._jornada(operario, ahora), ahora)

    def _jornada(self, operario: dict, ahora) -> _Jornada:
        """La jornada vigente del operario, la zona horaria de la empresa, sus turnos y sus
        actividades de esa jornada, presentadas con su estado personal (ActividadService cierra
        antes las jornadas que ya terminaron)."""
        empresa = self.empresa_repository.find_by_id(operario["empresa_id"]) or {}
        zona = empresa.get("zona_horaria") or ZONA_POR_DEFECTO
        turnos = self.turno_service.turnos_de_operarios([operario["id"]])
        fecha = turnos.jornada_vigente(operario["id"], ahora, zona)
        actividades = self.actividad_service.listar_actividades(
            {"fecha_desde": fecha, "fecha_hasta": fecha}, operario,
        )
        return _Jornada(fecha, zona, actividades, turnos)

    def _armar(self, operario: dict, jornada: _Jornada, ahora, orden=None) -> dict:
        """La programación de la jornada. Con "orden" se usa ese orden (vista previa); sin él, el
        que el operario guardó."""
        fecha, zona, turnos = jornada.fecha, jornada.zona, jornada.turnos
        orden = orden or self._orden_de(operario["id"], fecha)
        turno = turnos.turno_de(operario["id"], fecha)
        cierre = turnos.cierre_de([operario["id"]], fecha, zona)
        turno_hoy = _turno_de_hoy(turno, fecha, zona)
        programacion = programar_dia(jornada.actividades, orden, ahora, fecha, zona,
                                     turnos.capacidad_de(operario["id"], fecha), cierre,
                                     inicio_turno=turno_hoy["inicio"] if turno_hoy else None)
        asistencia = self.asistencia_service.actual(operario["id"], fecha, ahora)
        # Lo que pasaría del fin del turno: cuánto tendría que quedarse el operario (alcance, Sección 5.1).
        fin_turno = turno_hoy["fin"] if turno_hoy else None
        for tramo in programacion["tramos"]:
            tramo["fuera_del_turno_min"] = _minutos_fuera_del_turno(tramo, fin_turno)
        programacion["resumen"]["fuera_del_turno_min"] = sum(
            tramo["fuera_del_turno_min"] for tramo in programacion["tramos"])
        return {
            "fecha": fecha,
            "operario_id": operario["id"],
            "orden_personalizado": orden.es_personalizado,
            "tramos": programacion["tramos"],
            "resumen": programacion["resumen"],
            "actividades": jornada.actividades,
            "turno": turno_hoy,
            "asistencia": asistencia,
            "en_turno": bool(turno_hoy) and turno_hoy["inicio"] <= ahora < turno_hoy["fin"],
            "retraso_entrada_min": _minutos_de_retraso(turno_hoy, asistencia, fecha, ahora),
            "tolerancia_entrada_min": TOLERANCIA_ENTRADA_MIN,
        }

    def _orden_de(self, usuario_id: str, fecha: str) -> OrdenJornada:
        """El orden que el operario guardó para esa jornada; sin uno guardado, queda vacío y vale
        el sugerido. Se busca por fecha: el de otro día nunca se usa."""
        doc = self.orden_jornada_repository.find_de_usuario(usuario_id, fecha)
        return OrdenJornada.desde_documento(doc) if doc else OrdenJornada(usuario_id, fecha)
