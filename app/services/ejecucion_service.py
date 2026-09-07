from datetime import datetime, timezone

from app.models.ejecucion import Ejecucion
from app.models.enums import EstadoActividad, EstadoEjecucion
from app.utils.errors import NotFoundError, ValidationError


class EjecucionService:
    def __init__(self, ejecucion_repository, actividad_repository, asignacion_repository):
        self.ejecucion_repository = ejecucion_repository
        self.actividad_repository = actividad_repository
        self.asignacion_repository = asignacion_repository

    def iniciar(self, actividad_id: str) -> dict:
        if not self.actividad_repository.find_by_id(actividad_id):
            raise NotFoundError(f"Actividad {actividad_id} no encontrada")

        if not self.asignacion_repository.find_by_actividad(actividad_id):
            raise ValidationError("La actividad debe tener una asignación antes de iniciar ejecución")

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
        return self.obtener_ejecucion(ejecucion_id)

    def finalizar(self, actividad_id: str) -> dict:
        existente = self.ejecucion_repository.find_by_actividad(actividad_id)
        if not existente:
            raise NotFoundError(f"No hay ejecución en curso para la actividad {actividad_id}")

        ahora = datetime.now(timezone.utc)
        self.ejecucion_repository.update(
            str(existente["_id"]),
            {"estado": EstadoEjecucion.FINALIZADA.value, "fecha_fin": ahora},
        )
        self.actividad_repository.update(actividad_id, {"estado": EstadoActividad.COMPLETADA.value})
        return self.obtener_ejecucion(str(existente["_id"]))

    def obtener_ejecucion(self, ejecucion_id: str) -> dict:
        doc = self.ejecucion_repository.find_by_id(ejecucion_id)
        if not doc:
            raise NotFoundError(f"Ejecución {ejecucion_id} no encontrada")
        return Ejecucion.from_doc(doc)

    def obtener_por_actividad(self, actividad_id: str) -> dict:
        doc = self.ejecucion_repository.find_by_actividad(actividad_id)
        if not doc:
            raise NotFoundError(f"No hay ejecución para la actividad {actividad_id}")
        return Ejecucion.from_doc(doc)
