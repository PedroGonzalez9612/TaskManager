"""Registro de asistencia (alcance, Sección 5.1): el operario marca su entrada y su salida de cada
jornada con la hora del servidor, y el Administrador valida o corrige cada marca.

El turno no limita las marcas: se puede marcar entrada o salida fuera del horario del turno."""
from datetime import date, timedelta

from app.models.asistencia import Asistencia
from app.models.enums import Rol
from app.models.pausa import en_utc
from app.services.turno_service import resumen_turno
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError
from app.utils.fechas import validar_fecha, validar_hora
from app.utils.reloj import ZONA_POR_DEFECTO, ahora_utc, fecha_local, momento_local

# Estado con el que aparece en la lista del Administrador un operario con turno que no marcó entrada.
SIN_MARCA = "SIN_MARCA"
CAMBIO_SIMULTANEO = "La asistencia cambió mientras hacías esto. Actualiza la pantalla e inténtalo de nuevo."


def _dia_siguiente(fecha: str) -> str:
    return (date.fromisoformat(fecha) + timedelta(days=1)).isoformat()


class AsistenciaService:
    def __init__(self, asistencia_repository, turno_service, usuario_repository, empresa_repository, reloj=None):
        self.asistencia_repository = asistencia_repository
        self.turno_service = turno_service
        self.usuario_repository = usuario_repository
        self.empresa_repository = empresa_repository
        # La hora la pone el servidor. Las pruebas pasan un reloj que ellas controlan.
        self.reloj = reloj or ahora_utc

    # ---------- Marcas del Operario ----------

    def marcar_entrada(self, solicitante: dict) -> dict:
        """Abre la asistencia de hoy (el día de la empresa) con la hora del servidor. Si quedó
        abierta la de una jornada anterior, primero hay que marcar esa salida."""
        self._exigir_rol(solicitante, Rol.OPERARIO, "Solo el operario marca su entrada")
        ahora = self.reloj()
        jornada = fecha_local(ahora, self._zona_de(solicitante["empresa_id"]))
        abierta = self._abierta_de(solicitante["id"])
        if abierta and abierta.jornada != jornada:
            raise ValidationError(f"Tienes una salida pendiente de la jornada {abierta.jornada}. Márcala primero.")
        if abierta or self.asistencia_repository.find_de_usuario_en(solicitante["id"], jornada):
            raise ValidationError("Ya marcaste la entrada de hoy")

        asistencia = Asistencia(solicitante["id"], solicitante["empresa_id"], jornada, entrada=ahora)
        asistencia.id = self.asistencia_repository.insertar(asistencia.to_dict())
        if asistencia.id is None:
            # Otra marca de entrada del mismo operario llegó primero (índice único).
            raise ValidationError("Ya marcaste la entrada de hoy")
        return self.presentar(asistencia, ahora)

    def marcar_salida(self, solicitante: dict) -> dict:
        """Cierra la asistencia abierta del operario, aunque sea de la jornada anterior (un turno
        que cruza la medianoche se cierra al día siguiente)."""
        self._exigir_rol(solicitante, Rol.OPERARIO, "Solo el operario marca su salida")
        asistencia = self._abierta_de(solicitante["id"])
        if asistencia is None:
            raise ValidationError("No tienes una entrada abierta: marca primero la entrada")
        ahora = self.reloj()
        asistencia.marcar_salida(ahora)
        if not self.asistencia_repository.guardar(asistencia.id, asistencia.to_dict(), asistencia.estado.value,
                                                  solo_si_abierta=True):
            raise ValidationError(CAMBIO_SIMULTANEO)
        return self.presentar(asistencia, ahora)

    def consultar_hoy(self, solicitante: dict):
        """La asistencia abierta del operario o, si no tiene, la de hoy. None si no ha marcado."""
        self._exigir_rol(solicitante, Rol.OPERARIO, "Solo el operario consulta su asistencia")
        ahora = self.reloj()
        jornada = fecha_local(ahora, self._zona_de(solicitante["empresa_id"]))
        return self.actual(solicitante["id"], jornada, ahora)

    def actual(self, usuario_id: str, jornada: str, ahora):
        """La asistencia que importa ahora para el operario: la abierta (de hoy o de la jornada
        anterior) o, si no hay, la de esa jornada. Presentada, o None."""
        asistencia = self._abierta_de(usuario_id)
        if asistencia is None:
            doc = self.asistencia_repository.find_de_usuario_en(usuario_id, jornada)
            asistencia = Asistencia.desde_documento(doc) if doc else None
        return self.presentar(asistencia, ahora) if asistencia else None

    # ---------- Revisión del Administrador ----------

    def listar(self, solicitante: dict, jornada=None) -> list:
        """Las asistencias de la empresa en la jornada, con el nombre del operario, su turno vigente
        y el tiempo presente. Los operarios con turno que no marcaron aparecen como SIN_MARCA."""
        self._exigir_rol(solicitante, Rol.ADMINISTRADOR, "Solo el Administrador revisa la asistencia")
        empresa_id = solicitante["empresa_id"]
        ahora = self.reloj()
        jornada = validar_fecha(jornada, "La jornada") if jornada else fecha_local(ahora, self._zona_de(empresa_id))

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
            fila = self.presentar(asistencia, ahora) if asistencia else self._sin_marca(usuario_id, jornada)
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

    def _abierta_de(self, usuario_id: str):
        doc = self.asistencia_repository.find_abierta_de_usuario(usuario_id)
        return Asistencia.desde_documento(doc) if doc else None

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
