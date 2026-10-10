from datetime import datetime, timezone

from app.models.asignacion import Asignacion
from app.models.ejecucion import Ejecucion
from app.models.enums import EstadoActividad, EstadoAsignacion, EstadoEjecucion
from app.services.catalogo_service import MOTIVO_PAUSA, resolver_motivo
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError


class EjecucionService:
    """Lo que el operario hace con una actividad que tiene asignada: iniciarla, pausarla, reanudarla
    y finalizarla, o devolverla antes de iniciarla (alcance, Sección 5.1).

    La ejecución pertenece a la asignación: cada operario asignado tiene la suya, con su tiempo,
    sus pausas y su observación, así que lo que hace uno no cambia la de sus compañeros. El
    solicitante es siempre el operario que ejecuta. La hora de cada evento la pone el servidor
    (se lee el reloj una sola vez por operación).

    Las transiciones las valida la clase Ejecucion; este servicio comprueba lo que depende de
    otros datos (la asignación, la actividad, las demás ejecuciones del operario) y guarda.
    Después de cada evento le pide a ActividadService que recalcule el estado de la actividad y
    devuelve la actividad tal como la ve ese operario."""

    def __init__(self, ejecucion_repository, actividad_repository, asignacion_repository,
                 actividad_service, catalogo_service, cierre_jornada, reloj=None):
        self.ejecucion_repository = ejecucion_repository
        self.actividad_repository = actividad_repository
        self.asignacion_repository = asignacion_repository
        self.actividad_service = actividad_service
        self.catalogo_service = catalogo_service
        self.cierre_jornada = cierre_jornada
        self.reloj = reloj or (lambda: datetime.now(timezone.utc))

    # ---------- Eventos ----------

    def iniciar(self, actividad_id: str, solicitante: dict) -> dict:
        ahora = self._ahora_con_la_jornada_cerrada(solicitante)
        actividad, asignacion_id = self._actividad_y_asignacion(actividad_id, solicitante)
        if EstadoActividad(actividad.get("estado", EstadoActividad.PENDIENTE.value)).es_final:
            raise ValidationError("Esta actividad ya está cerrada y no se puede iniciar")
        self._exigir_sin_ejecucion(asignacion_id)
        self._exigir_sin_otra_en_curso(solicitante, "iniciar")

        ejecucion = Ejecucion(actividad_id=actividad_id, asignacion_id=asignacion_id,
                              usuario_id=solicitante["id"], fecha_inicio=ahora)
        if self.ejecucion_repository.insertar_en_progreso(ejecucion.to_dict()) is None:
            # Dos peticiones al tiempo pasaron las comprobaciones: la base de datos rechazó esta.
            self._exigir_sin_otra_en_curso(solicitante, "iniciar")
            raise ValidationError("Ya iniciaste esta actividad")
        return self._actividad_actualizada(actividad_id, solicitante)

    def pausar(self, actividad_id: str, solicitante: dict, motivo, detalle=None) -> dict:
        ahora = self._ahora_con_la_jornada_cerrada(solicitante)
        actividad, asignacion_id = self._actividad_y_asignacion(actividad_id, solicitante)
        ejecucion = self._ejecucion_iniciada(asignacion_id)
        if actividad.get("hora_programada"):
            raise ValidationError("Una actividad de hora fija no se puede pausar")

        elegido = resolver_motivo(motivo, detalle)
        ejecucion.pausar(elegido.texto, ahora)    # Valida que esté en curso y que haya motivo.
        self._guardar(ejecucion, EstadoEjecucion.EN_PROGRESO)
        # Lo que se escribió en "Otro" queda en la lista de motivos de la empresa.
        self.catalogo_service.registrar_motivo(solicitante["empresa_id"], MOTIVO_PAUSA, elegido)
        return self._actividad_actualizada(actividad_id, solicitante)

    def reanudar(self, actividad_id: str, solicitante: dict) -> dict:
        ahora = self._ahora_con_la_jornada_cerrada(solicitante)
        _, asignacion_id = self._actividad_y_asignacion(actividad_id, solicitante)
        ejecucion = self._ejecucion_iniciada(asignacion_id)

        ejecucion.reanudar(ahora)    # Valida que esté pausada.
        self._exigir_sin_otra_en_curso(solicitante, "reanudar")
        if not self.ejecucion_repository.guardar(
                ejecucion.id, ejecucion.to_dict(), estado_esperado=EstadoEjecucion.PAUSADA.value):
            # Otra petición inició o reanudó una actividad al mismo tiempo, o esta ya no estaba pausada.
            self._exigir_sin_otra_en_curso(solicitante, "reanudar")
            raise ValidationError("Ya tienes otra actividad en curso. Páusala o finalízala antes de reanudar esta.")
        return self._actividad_actualizada(actividad_id, solicitante)

    def finalizar(self, actividad_id: str, solicitante: dict, observacion=None) -> dict:
        ahora = self._ahora_con_la_jornada_cerrada(solicitante)
        _, asignacion_id = self._actividad_y_asignacion(actividad_id, solicitante)
        ejecucion = self._ejecucion_iniciada(asignacion_id)

        ejecucion.finalizar(ahora, observacion)    # Valida que esté en curso.
        self._guardar(ejecucion, EstadoEjecucion.EN_PROGRESO)
        return self._actividad_actualizada(actividad_id, solicitante)

    def devolver(self, actividad_id: str, solicitante: dict, motivo, detalle=None) -> dict:
        """El operario devuelve la actividad antes de iniciarla. Solo sale él: si la actividad tiene
        más operarios, sigue con ellos; si no queda ninguno, vuelve al Administrador (DEVUELTA).

        Quien devuelve deja de ver la actividad, por eso no se responde con ella sino con la
        constancia de la devolución."""
        ahora = self._ahora_con_la_jornada_cerrada(solicitante)
        actividad, documento = self._actividad_y_documento_de_asignacion(actividad_id, solicitante)
        if EstadoActividad(actividad.get("estado", EstadoActividad.PENDIENTE.value)).es_final:
            raise ValidationError("Esta actividad ya está cerrada y no se puede devolver")
        asignacion = Asignacion.desde_documento(documento)
        if self.ejecucion_repository.find_by_asignacion(asignacion.id):
            raise ValidationError("Solo puedes devolver una actividad antes de iniciarla")

        # La lista de motivos de devolución es fija: lo escrito en "Otro" no se agrega a ningún catálogo.
        asignacion.devolver(resolver_motivo(motivo, detalle).texto, ahora)    # Valida que haya motivo.
        devuelta = self.asignacion_repository.actualizar_si(
            asignacion.id, {"estado": EstadoAsignacion.ACTIVA.value}, asignacion.to_dict(),
        )
        if not devuelta:
            raise ValidationError("Esta actividad ya no está asignada a ti. Actualiza la pantalla.")

        self.actividad_service.recalcular_estado(actividad_id, por_devolucion=True)
        return {
            "actividad_id": actividad_id,
            "devuelta": True,
            **asignacion.devolucion.to_dict(),
        }

    # ---------- Comprobaciones ----------

    def _actividad_y_asignacion(self, actividad_id: str, solicitante: dict) -> tuple:
        """La actividad (de la empresa del operario) y el id de su asignación activa a ella."""
        actividad, asignacion = self._actividad_y_documento_de_asignacion(actividad_id, solicitante)
        return actividad, str(asignacion["_id"])

    def _actividad_y_documento_de_asignacion(self, actividad_id: str, solicitante: dict) -> tuple:
        actividad = self.actividad_repository.find_by_id(actividad_id)
        if not actividad or actividad.get("empresa_id") != solicitante["empresa_id"]:
            raise NotFoundError("La actividad no existe")
        asignacion = self.asignacion_repository.find_activa(actividad_id, solicitante["id"])
        if not asignacion:
            raise ProhibidoError("Esta actividad no está asignada a ti")
        return actividad, asignacion

    def _ejecucion_iniciada(self, asignacion_id: str) -> Ejecucion:
        doc = self.ejecucion_repository.find_by_asignacion(asignacion_id)
        if not doc:
            raise ValidationError("Todavía no has iniciado esta actividad")
        return Ejecucion.desde_documento(doc)

    def _exigir_sin_ejecucion(self, asignacion_id: str) -> None:
        """Hay una sola ejecución por asignación: iniciar es solo la primera vez."""
        doc = self.ejecucion_repository.find_by_asignacion(asignacion_id)
        if not doc:
            return
        estado = Ejecucion.desde_documento(doc).estado
        if estado == EstadoEjecucion.PAUSADA:
            raise ValidationError("Ya iniciaste esta actividad y la tienes pausada: reanúdala")
        if estado == EstadoEjecucion.EN_PROGRESO:
            raise ValidationError("Ya tienes esta actividad en curso")
        raise ValidationError("Ya terminaste esta actividad")

    def _exigir_sin_otra_en_curso(self, solicitante: dict, accion: str) -> None:
        """Un operario tiene una sola actividad en ejecución a la vez (alcance, Sección 5.1)."""
        en_curso = self.ejecucion_repository.find_en_progreso_de_usuario(solicitante["id"])
        if not en_curso:
            return
        actividad = self.actividad_repository.find_by_id(en_curso["actividad_id"])
        cual = ""
        if actividad:
            cual = " (" + " ".join(filter(None, [actividad.get("codigo"), actividad.get("titulo")])) + ")"
        raise ValidationError(
            f"Ya tienes una actividad en curso{cual}. Páusala o finalízala antes de {accion} otra."
        )

    # ---------- Apoyo ----------

    def _ahora_con_la_jornada_cerrada(self, solicitante: dict):
        """La hora del servidor para este evento. Antes cierra lo que quedó abierto en días
        anteriores (alcance, Sección 5.1): así ningún operario actúa sobre una ejecución en curso
        de otro día. Es el único punto de este servicio que llama al cierre."""
        self.cierre_jornada.cerrar_pendientes(solicitante["empresa_id"])
        return self.reloj()

    def _guardar(self, ejecucion: Ejecucion, estado_esperado: EstadoEjecucion) -> None:
        guardada = self.ejecucion_repository.guardar(
            ejecucion.id, ejecucion.to_dict(), estado_esperado=estado_esperado.value,
        )
        if not guardada:
            raise ValidationError("La actividad cambió mientras hacías esto. Actualiza la pantalla e inténtalo de nuevo.")

    def _actividad_actualizada(self, actividad_id: str, solicitante: dict) -> dict:
        self.actividad_service.recalcular_estado(actividad_id)
        return self.actividad_service.obtener_actividad(actividad_id, solicitante)
