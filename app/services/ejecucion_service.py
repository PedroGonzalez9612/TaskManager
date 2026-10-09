from datetime import datetime, timezone

from app.models.ejecucion import Ejecucion
from app.models.enums import EstadoActividad, EstadoEjecucion
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError


class EjecucionService:
    """Inicio y fin de la ejecución de una actividad. La hora de cada evento la pone el servidor.

    PENDIENTE (decisión de diseño abierta): hoy la ejecución pertenece a la actividad. Falta decidir si
    debe pertenecer a la asignación (operario + actividad) antes de agregar las pausas."""

    def __init__(self, ejecucion_repository, actividad_repository, asignacion_repository):
        self.ejecucion_repository = ejecucion_repository
        self.actividad_repository = actividad_repository
        self.asignacion_repository = asignacion_repository

    def iniciar(self, actividad_id: str, solicitante: dict) -> dict:
        actividad = self._actividad_asignada(actividad_id, solicitante)
        if actividad["estado"] == EstadoActividad.COMPLETADA.value:
            raise ValidationError("Esta actividad ya fue finalizada")
        if actividad["estado"] == EstadoActividad.EN_EJECUCION.value:
            raise ValidationError("Esta actividad ya está en curso")
        self._verificar_sin_actividad_en_curso(solicitante)

        existente = self.ejecucion_repository.find_by_actividad(actividad_id)
        ahora = datetime.now(timezone.utc)
        if existente:
            self.ejecucion_repository.update(
                str(existente["_id"]),
                {"estado": EstadoEjecucion.EN_PROGRESO.value, "fecha_inicio": ahora, "fecha_fin": None},
            )
            ejecucion_id = str(existente["_id"])
        else:
            ejecucion = Ejecucion(actividad_id=actividad_id, estado=EstadoEjecucion.EN_PROGRESO, fecha_inicio=ahora)
            ejecucion_id = self.ejecucion_repository.insert(ejecucion.to_dict())

        self.actividad_repository.update(actividad_id, {"estado": EstadoActividad.EN_EJECUCION.value})
        return Ejecucion.from_doc(self.ejecucion_repository.find_by_id(ejecucion_id))

    def finalizar(self, actividad_id: str, solicitante: dict) -> dict:
        actividad = self._actividad_asignada(actividad_id, solicitante)
        existente = self.ejecucion_repository.find_by_actividad(actividad_id)
        if actividad["estado"] != EstadoActividad.EN_EJECUCION.value or not existente:
            raise ValidationError("Solo se puede finalizar una actividad que esté en curso")

        self.ejecucion_repository.update(
            str(existente["_id"]),
            {"estado": EstadoEjecucion.FINALIZADA.value, "fecha_fin": datetime.now(timezone.utc)},
        )
        self.actividad_repository.update(actividad_id, {"estado": EstadoActividad.COMPLETADA.value})
        return Ejecucion.from_doc(self.ejecucion_repository.find_by_id(str(existente["_id"])))

    def _actividad_asignada(self, actividad_id: str, solicitante: dict) -> dict:
        actividad = self.actividad_repository.find_by_id(actividad_id)
        if not actividad or actividad.get("empresa_id") != solicitante["empresa_id"]:
            raise NotFoundError("La actividad no existe")
        if not self.asignacion_repository.existe(actividad_id, solicitante["id"]):
            raise ProhibidoError("Esta actividad no está asignada a ti")
        return actividad

    def _verificar_sin_actividad_en_curso(self, solicitante: dict) -> None:
        """Un operario tiene una sola actividad en ejecución a la vez (alcance, Sección 5.1)."""
        ids = [a["actividad_id"] for a in self.asignacion_repository.find_by_usuario(solicitante["id"])]
        for actividad in self.actividad_repository.buscar(solicitante["empresa_id"], ids=ids):
            if actividad.get("estado") == EstadoActividad.EN_EJECUCION.value:
                raise ValidationError(
                    f"Ya tienes una actividad en curso ({actividad.get('codigo', '')} {actividad['titulo']}). "
                    f"Finalízala antes de iniciar otra."
                )
