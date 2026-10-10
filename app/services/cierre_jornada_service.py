"""Cierre de la jornada (alcance, Sección 5.1): qué pasa con lo que no se terminó en su día.

No hay un proceso en segundo plano: los demás servicios llaman a cerrar_pendientes() antes de leer
o cambiar las actividades de una empresa. Si no hay nada atrasado, sale después de dos consultas
cortas (la zona horaria de la empresa y las actividades abiertas de días anteriores)."""
from app.models.actividad import Actividad
from app.models.ejecucion import Ejecucion
from app.models.enums import MOTIVO_PAUSA_FIN_JORNADA, EstadoEjecucion
from app.models.pausa import en_utc
from app.services.estado_actividad import calcular_estado_actividad
from app.utils.reloj import ZONA_POR_DEFECTO, ahora_utc, fecha_local, fin_del_dia

CONTEOS = ("reprogramadas", "no_realizadas", "ejecuciones_pausadas", "ejecuciones_cerradas")

# Solo se escriben los campos que el cierre cambia, para no pisar una edición hecha al mismo tiempo.
CAMPOS_REPROGRAMACION = ("fecha_programada", "fecha_original", "reprogramaciones", "estado")
CAMPOS_NO_REALIZADA = ("estado", "fecha_no_realizada")


def momento_de_cierre(ejecucion: Ejecucion, fin_jornada):
    """La hora con la que se pausa o se cierra una ejecución que quedó abierta: el fin de su
    jornada, no la hora en que alguien consultó, para no inflar el tiempo real. Si su último
    evento (inicio, pausa o reanudación) es posterior, se usa ese, para no dejar tiempos negativos."""
    eventos = [ejecucion.fecha_inicio]
    for pausa in ejecucion.pausas:
        eventos.extend([pausa.inicio, pausa.fin])
    return max([fin_jornada] + [en_utc(evento) for evento in eventos if evento is not None])


class CierreJornadaService:
    """Reprograma las actividades de horario flexible que no se terminaron y deja como No realizadas las de
    hora fija. Mientras no existan los turnos, la jornada termina con el día en la zona horaria
    de la empresa.

    No depende de ActividadService (que es quien lo llama): el estado de una actividad reprogramada
    lo calcula con la misma función pura de estado_actividad.py."""

    def __init__(self, actividad_repository, asignacion_repository, ejecucion_repository,
                 empresa_repository, reloj=None):
        self.actividad_repository = actividad_repository
        self.asignacion_repository = asignacion_repository
        self.ejecucion_repository = ejecucion_repository
        self.empresa_repository = empresa_repository
        self.reloj = reloj or ahora_utc

    def cerrar_pendientes(self, empresa_id: str) -> dict:
        """Cierra lo que quedó abierto en días anteriores a hoy y devuelve cuánto hizo. Se puede
        llamar las veces que sea: lo que ya se cerró no se vuelve a tocar."""
        resultado = dict.fromkeys(CONTEOS, 0)
        if not empresa_id:
            return resultado
        ahora = self.reloj()
        zona = self._zona_de(empresa_id)
        hoy = fecha_local(ahora, zona)

        for doc in self.actividad_repository.buscar_abiertas_anteriores_a(empresa_id, hoy):
            actividad = Actividad.desde_documento(doc)
            # Solo se guarda si nadie más la movió ni le cambió el estado desde que se leyó: con
            # dos peticiones a la vez, una sola la cierra y la otra la salta.
            condicion = {"fecha_programada": doc.get("fecha_programada"), "estado": doc.get("estado")}
            fin_jornada = fin_del_dia(actividad.fecha_programada, zona)
            if actividad.es_hora_fija:
                self._dejar_no_realizada(actividad, condicion, fin_jornada, ahora, resultado)
            else:
                self._reprogramar(actividad, condicion, fin_jornada, hoy, ahora, resultado)
        return resultado

    # ---------- Hora fija: No realizada ----------

    def _dejar_no_realizada(self, actividad: Actividad, condicion: dict, fin_jornada, ahora, resultado: dict) -> None:
        """La actividad queda No realizada y lo que alguien llevaba abierto se cierra a la hora en
        que terminó su día: el tiempo trabajado se conserva."""
        actividad.marcar_no_realizada(ahora)
        if not self._guardar(actividad, condicion, CAMPOS_NO_REALIZADA):
            return
        resultado["no_realizadas"] += 1
        for ejecucion in self._ejecuciones_abiertas(actividad.id):
            estado_leido = ejecucion.estado.value
            ejecucion.cerrar(momento_de_cierre(ejecucion, fin_jornada))
            if self.ejecucion_repository.guardar(ejecucion.id, ejecucion.to_dict(), estado_esperado=estado_leido):
                resultado["ejecuciones_cerradas"] += 1

    # ---------- Horario flexible: actividad reprogramada ----------

    def _reprogramar(self, actividad: Actividad, condicion: dict, fin_jornada, hoy: str, ahora, resultado: dict) -> None:
        """Lo que alguien dejó en curso se pausa con el motivo "Fin de jornada" a la hora en que
        terminó su día, y la actividad pasa a hoy con una sola reprogramación, aunque hayan pasado varios
        días. Lo que ya estaba pausado no se toca."""
        en_curso = [
            ejecucion for ejecucion in self._ejecuciones_abiertas(actividad.id)
            if ejecucion.estado == EstadoEjecucion.EN_PROGRESO
        ]
        for ejecucion in en_curso:
            ejecucion.pausar(MOTIVO_PAUSA_FIN_JORNADA, momento_de_cierre(ejecucion, fin_jornada))
            if self.ejecucion_repository.guardar(
                    ejecucion.id, ejecucion.to_dict(), estado_esperado=EstadoEjecucion.EN_PROGRESO.value):
                resultado["ejecuciones_pausadas"] += 1

        actividad.reprogramar(hoy, ahora)
        if en_curso:
            # Se calcula con lo que quedó guardado, por si otra petición pausó al mismo tiempo.
            actividad.estado = self._estado_segun_ejecuciones(actividad)
        if self._guardar(actividad, condicion, CAMPOS_REPROGRAMACION):
            resultado["reprogramadas"] += 1

    def _estado_segun_ejecuciones(self, actividad: Actividad):
        estado_por_asignacion = {
            ejecucion.get("asignacion_id"): ejecucion.get("estado")
            for ejecucion in self.ejecucion_repository.find_by_actividades([actividad.id])
        }
        asignaciones = self.asignacion_repository.find_by_actividad(actividad.id)
        return calcular_estado_actividad(
            actividad.estado, [estado_por_asignacion.get(str(asignacion["_id"])) for asignacion in asignaciones],
        )

    # ---------- Apoyo ----------

    def _zona_de(self, empresa_id: str) -> str:
        empresa = self.empresa_repository.find_by_id(empresa_id) or {}
        return empresa.get("zona_horaria") or ZONA_POR_DEFECTO

    def _ejecuciones_abiertas(self, actividad_id: str) -> list:
        return [
            Ejecucion.desde_documento(doc)
            for doc in self.ejecucion_repository.find_abiertas_de_actividad(actividad_id)
        ]

    def _guardar(self, actividad: Actividad, condicion: dict, campos: tuple) -> bool:
        datos = actividad.to_dict()
        cambios = {campo: datos[campo] for campo in campos}
        return self.actividad_repository.actualizar_si(actividad.id, condicion, cambios)
