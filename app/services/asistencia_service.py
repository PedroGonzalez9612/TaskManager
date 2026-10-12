"""Registro de asistencia (alcance, Sección 5.1): el operario marca su entrada y su salida de cada
jornada con la hora del servidor, y el Administrador valida o corrige cada marca.

El turno no limita las marcas: se puede marcar entrada o salida fuera del horario del turno. Lo que
sí decide es la jornada vigente: con un turno de noche, después de la medianoche las marcas siguen
siendo de la jornada en que empezó el turno."""
from datetime import date, timedelta

from app.models.asistencia import Asistencia
from app.models.enums import Rol
from app.models.pausa import en_utc
from app.services.turno_service import dia_anterior, resumen_turno
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError
from app.utils.fechas import validar_fecha, validar_hora
from app.utils.reloj import ZONA_POR_DEFECTO, ahora_utc, fecha_local, momento_local

# Estados con los que aparece una fila en la lista del Administrador (solo de presentación, no se
# guardan): un operario con turno que no marcó entrada, y una asistencia de una jornada que ya
# pasó y quedó sin salida, para que la corrija.
SIN_MARCA = "SIN_MARCA"
SIN_SALIDA = "SIN_SALIDA"
CAMBIO_SIMULTANEO = "La asistencia cambió mientras hacías esto. Actualiza la pantalla e inténtalo de nuevo."
YA_MARCO_ENTRADA = "Ya marcaste la entrada de esta jornada"
SIN_ENTRADA = "Marca tu entrada para empezar"
YA_MARCO_SALIDA = "Ya marcaste la salida de esta jornada"
SALIDA_CON_ACTIVIDAD_EN_CURSO = "Tienes una actividad en curso. Finalízala o páusala antes de marcar la salida."


def _dia_siguiente(fecha: str) -> str:
    return (date.fromisoformat(fecha) + timedelta(days=1)).isoformat()


class AsistenciaService:
    def __init__(self, asistencia_repository, turno_service, usuario_repository, empresa_repository,
                 ejecucion_repository, reloj=None):
        self.asistencia_repository = asistencia_repository
        # Solo para saber si el operario tiene algo en curso al marcar la salida.
        self.ejecucion_repository = ejecucion_repository
        self.turno_service = turno_service
        self.usuario_repository = usuario_repository
        self.empresa_repository = empresa_repository
        # La hora la pone el servidor. Las pruebas pasan un reloj que ellas controlan.
        self.reloj = reloj or ahora_utc

    # ---------- Marcas del Operario ----------

    def marcar_entrada(self, solicitante: dict) -> dict:
        """Abre la asistencia de la jornada vigente con la hora del servidor; hay una sola por
        jornada. Una asistencia de una jornada anterior que quedó sin salida no lo impide: sigue
        abierta para que el Administrador la corrija."""
        self._exigir_rol(solicitante, Rol.OPERARIO, "Solo el operario marca su entrada")
        ahora = self.reloj()
        jornada = self._jornada_vigente(solicitante, ahora)
        if self._de_la_jornada(solicitante["id"], jornada):
            raise ValidationError(YA_MARCO_ENTRADA)

        asistencia = Asistencia(solicitante["id"], solicitante["empresa_id"], jornada, entrada=ahora)
        asistencia.id = self.asistencia_repository.insertar(asistencia.to_dict())
        if asistencia.id is None:
            # Otra marca de entrada del mismo operario llegó primero (índice único).
            raise ValidationError(YA_MARCO_ENTRADA)
        return self.presentar(asistencia, ahora)

    def marcar_salida(self, solicitante: dict) -> dict:
        """Cierra la asistencia de la jornada vigente o, si esa no existe, la abierta de la jornada
        inmediatamente anterior (turno nocturno o tiempo adicional). Nunca una más antigua."""
        self._exigir_rol(solicitante, Rol.OPERARIO, "Solo el operario marca su salida")
        ahora = self.reloj()
        asistencia = self._la_que_corresponde(solicitante["id"], self._jornada_vigente(solicitante, ahora))
        if asistencia is None:
            raise ValidationError("No tienes una entrada abierta en esta jornada: marca primero la entrada")
        # Las pausadas no lo impiden: el cierre de jornada las reprograma.
        if self.ejecucion_repository.find_en_progreso_de_usuario(solicitante["id"]):
            raise ValidationError(SALIDA_CON_ACTIVIDAD_EN_CURSO)
        asistencia.marcar_salida(ahora)
        if not self.asistencia_repository.guardar(asistencia.id, asistencia.to_dict(), asistencia.estado.value,
                                                  solo_si_abierta=True):
            raise ValidationError(CAMBIO_SIMULTANEO)
        return self.presentar(asistencia, ahora)

    def consultar_hoy(self, solicitante: dict):
        """La asistencia de la jornada vigente o, si no la hay, la abierta de la jornada anterior.
        None si no ha marcado."""
        self._exigir_rol(solicitante, Rol.OPERARIO, "Solo el operario consulta su asistencia")
        ahora = self.reloj()
        return self.actual(solicitante["id"], self._jornada_vigente(solicitante, ahora), ahora)

    def exigir_entrada_abierta(self, solicitante: dict, ahora) -> None:
        """Para iniciar o reanudar una actividad el operario debe tener marcada la entrada de su
        jornada vigente y no haber marcado la salida (alcance, Sección 5.1). El turno no limita:
        no importa a qué hora la marcó."""
        asistencia = self._la_que_corresponde(solicitante["id"], self._jornada_vigente(solicitante, ahora))
        if asistencia is None:
            raise ValidationError(SIN_ENTRADA)
        if not asistencia.esta_abierta:
            raise ValidationError(YA_MARCO_SALIDA)

    def actual(self, usuario_id: str, jornada: str, ahora):
        """La asistencia que importa ahora para el operario en su jornada vigente "jornada": la de
        esa jornada o, si no existe, la abierta de la jornada anterior. Presentada, o None."""
        asistencia = self._la_que_corresponde(usuario_id, jornada)
        return self.presentar(asistencia, ahora) if asistencia else None

    # ---------- Revisión del Administrador ----------

    def listar(self, solicitante: dict, jornada=None) -> list:
        """Las asistencias de la empresa en la jornada, con el nombre del operario, su turno vigente
        y el tiempo presente. Los operarios con turno que no marcaron aparecen como SIN_MARCA, y una
        asistencia de una jornada anterior a la vigente del operario que sigue sin salida, como SIN_SALIDA."""
        self._exigir_rol(solicitante, Rol.ADMINISTRADOR, "Solo el Administrador revisa la asistencia")
        empresa_id = solicitante["empresa_id"]
        ahora = self.reloj()
        zona = self._zona_de(empresa_id)
        jornada = validar_fecha(jornada, "La jornada") if jornada else fecha_local(ahora, zona)

        operarios = self.usuario_repository.find_by_empresa_y_rol(empresa_id, Rol.OPERARIO.value)
        turnos = self.turno_service.turnos_de_operarios([str(o["_id"]) for o in operarios])
        por_usuario = {doc["usuario_id"]: Asistencia.desde_documento(doc)
                       for doc in self.asistencia_repository.find_de_empresa_en(empresa_id, jornada)}

        filas = []
        for operario in operarios:
            usuario_id = str(operario["_id"])
            turno = turnos.turno_de(usuario_id, jornada)
            asistencia = por_usuario.get(usuario_id)
            if asistencia is None and turno is None:
                continue                        # Sin turno ni marca: no se esperaba que viniera.
            if asistencia is None:
                fila = self._sin_marca(usuario_id, jornada)
            else:
                fila = self._fila(asistencia, turnos.jornada_vigente(usuario_id, ahora, zona), ahora)
            filas.append({**fila, "operario": operario["nombre"], "turno": resumen_turno(turno)})
        return filas

    def validar(self, solicitante: dict, asistencia_id: str) -> dict:
        self._exigir_rol(solicitante, Rol.ADMINISTRADOR, "Solo el Administrador valida la asistencia")
        asistencia = self._asistencia_de_la_empresa(asistencia_id, solicitante)
        estado_anterior = asistencia.estado.value
        ahora = self.reloj()
        asistencia.validar(solicitante["id"], ahora)
        return self._guardar_revision(asistencia, estado_anterior, ahora)

    def corregir(self, solicitante: dict, asistencia_id: str, entrada, salida, motivo) -> dict:
        """Corrige las marcas. "entrada" y "salida" llegan como "HH:MM" en la hora de la empresa,
        en la jornada de la asistencia; una salida menor que la entrada es del día siguiente (turno
        de noche). La salida puede venir vacía: la asistencia queda abierta."""
        self._exigir_rol(solicitante, Rol.ADMINISTRADOR, "Solo el Administrador corrige la asistencia")
        asistencia = self._asistencia_de_la_empresa(asistencia_id, solicitante)
        zona = self._zona_de(solicitante["empresa_id"])
        momento_entrada, momento_salida = self._momentos(asistencia.jornada, entrada, salida, zona)
        ahora = self.reloj()
        if max(momento_entrada, momento_salida or momento_entrada) > ahora:
            raise ValidationError("Una marca corregida no puede quedar después de la hora actual")
        estado_anterior = asistencia.estado.value
        asistencia.corregir(momento_entrada, momento_salida, motivo, solicitante["id"], ahora)
        return self._guardar_revision(asistencia, estado_anterior, ahora)

    # ---------- Presentación ----------

    @staticmethod
    def presentar(asistencia: Asistencia, ahora) -> dict:
        """Las marcas van en UTC (MongoDB las devuelve sin zona)."""
        return {
            "id": asistencia.id, "usuario_id": asistencia.usuario_id, "jornada": asistencia.jornada,
            "entrada": en_utc(asistencia.entrada), "salida": en_utc(asistencia.salida),
            "estado": asistencia.estado.value,
            "minutos_presente": asistencia.minutos_presente(ahora), "revision": asistencia.revision,
        }

    @classmethod
    def _fila(cls, asistencia: Asistencia, jornada_vigente: str, ahora) -> dict:
        """La asistencia para la lista del Administrador. Si es de una jornada que ya pasó para el
        operario y sigue sin salida, se muestra como SIN_SALIDA (el estado guardado no cambia)."""
        fila = cls.presentar(asistencia, ahora)
        if asistencia.esta_abierta and asistencia.jornada < jornada_vigente:
            fila["estado"] = SIN_SALIDA
        return fila

    @staticmethod
    def _sin_marca(usuario_id: str, jornada: str) -> dict:
        return {
            "id": None, "usuario_id": usuario_id, "jornada": jornada, "entrada": None, "salida": None,
            "estado": SIN_MARCA, "minutos_presente": 0, "revision": None,
        }

    # ---------- Apoyo ----------

    @staticmethod
    def _momentos(jornada: str, entrada, salida, zona) -> tuple:
        """Convierte las horas "HH:MM" de la corrección en momentos UTC de esa jornada."""
        hora_entrada = validar_hora(entrada, "La hora de entrada")
        momento_entrada = momento_local(jornada, hora_entrada, zona)
        if salida in (None, ""):
            return momento_entrada, None
        hora_salida = validar_hora(salida, "La hora de salida")
        dia_salida = _dia_siguiente(jornada) if hora_salida < hora_entrada else jornada
        return momento_entrada, momento_local(dia_salida, hora_salida, zona)

    def _guardar_revision(self, asistencia: Asistencia, estado_anterior: str, ahora) -> dict:
        if not self.asistencia_repository.guardar(asistencia.id, asistencia.to_dict(), estado_anterior):
            raise ValidationError(CAMBIO_SIMULTANEO)
        return self.presentar(asistencia, ahora)

    def _jornada_vigente(self, solicitante: dict, ahora) -> str:
        zona = self._zona_de(solicitante["empresa_id"])
        return self.turno_service.jornada_vigente(solicitante["id"], ahora, zona)

    def _de_la_jornada(self, usuario_id: str, jornada: str):
        doc = self.asistencia_repository.find_de_usuario_en(usuario_id, jornada)
        return Asistencia.desde_documento(doc) if doc else None

    def _la_que_corresponde(self, usuario_id: str, jornada: str):
        """La asistencia de la jornada vigente o, si no existe, la abierta de la jornada
        inmediatamente anterior. Nunca una más antigua. None si no hay ninguna."""
        asistencia = self._de_la_jornada(usuario_id, jornada)
        if asistencia is not None:
            return asistencia
        anterior = self._de_la_jornada(usuario_id, dia_anterior(jornada))
        return anterior if anterior and anterior.esta_abierta else None

    def _asistencia_de_la_empresa(self, asistencia_id: str, solicitante: dict) -> Asistencia:
        doc = self.asistencia_repository.find_by_id(asistencia_id)
        if not doc or doc.get("empresa_id") != solicitante["empresa_id"]:
            raise NotFoundError("La asistencia no existe en tu empresa")
        return Asistencia.desde_documento(doc)

    @staticmethod
    def _exigir_rol(solicitante: dict, rol: Rol, mensaje: str) -> None:
        if solicitante["rol"] != rol.value:
            raise ProhibidoError(mensaje)

    def _zona_de(self, empresa_id: str) -> str:
        empresa = self.empresa_repository.find_by_id(empresa_id) or {}
        return empresa.get("zona_horaria") or ZONA_POR_DEFECTO
