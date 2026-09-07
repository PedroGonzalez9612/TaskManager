from app.models.actividad import Actividad
from app.models.enums import EstadoActividad, Prioridad
from app.utils.errors import NotFoundError, ValidationError


class ActividadService:
    def __init__(self, actividad_repository, requerimiento_repository):
        self.actividad_repository = actividad_repository
        self.requerimiento_repository = requerimiento_repository

    def crear_actividad(self, data: dict) -> dict:
        titulo = data.get("titulo")
        requerimiento_id = data.get("requerimiento_id")
        descripcion = data.get("descripcion", "")
        prioridad = data.get("prioridad", Prioridad.MEDIA.value)

        if not titulo or not requerimiento_id:
            raise ValidationError("titulo y requerimiento_id son obligatorios")

        if prioridad not in [p.value for p in Prioridad]:
            raise ValidationError(f"prioridad inválida: {prioridad}")

        if not self.requerimiento_repository.find_by_id(requerimiento_id):
            raise NotFoundError(f"Requerimiento {requerimiento_id} no encontrado")

        actividad = Actividad(
            titulo=titulo,
            descripcion=descripcion,
            requerimiento_id=requerimiento_id,
            prioridad=prioridad,
        )
        actividad_id = self.actividad_repository.insert(actividad.to_dict())
        return self.obtener_actividad(actividad_id)

    def obtener_actividad(self, actividad_id: str) -> dict:
        doc = self.actividad_repository.find_by_id(actividad_id)
        if not doc:
            raise NotFoundError(f"Actividad {actividad_id} no encontrada")
        return Actividad.from_doc(doc)

    def listar_actividades(self, requerimiento_id: str = None) -> list:
        docs = self.actividad_repository.find_by_requerimiento(requerimiento_id) if requerimiento_id \
            else self.actividad_repository.find_all()
        return [Actividad.from_doc(doc) for doc in docs]

    def actualizar_actividad(self, actividad_id: str, data: dict) -> dict:
        updates = {k: v for k, v in data.items() if k in ("titulo", "descripcion", "prioridad", "estado")}
        if "prioridad" in updates and updates["prioridad"] not in [p.value for p in Prioridad]:
            raise ValidationError(f"prioridad inválida: {updates['prioridad']}")
        if "estado" in updates and updates["estado"] not in [e.value for e in EstadoActividad]:
            raise ValidationError(f"estado inválido: {updates['estado']}")
        if not updates:
            raise ValidationError("No hay campos válidos para actualizar")
        updated = self.actividad_repository.update(actividad_id, updates)
        if not updated:
            raise NotFoundError(f"Actividad {actividad_id} no encontrada")
        return self.obtener_actividad(actividad_id)

    def cambiar_estado(self, actividad_id: str, estado: str) -> dict:
        if estado not in [e.value for e in EstadoActividad]:
            raise ValidationError(f"estado inválido: {estado}")
        updated = self.actividad_repository.update(actividad_id, {"estado": estado})
        if not updated:
            raise NotFoundError(f"Actividad {actividad_id} no encontrada")
        return self.obtener_actividad(actividad_id)

    def eliminar_actividad(self, actividad_id: str) -> None:
        deleted = self.actividad_repository.delete(actividad_id)
        if not deleted:
            raise NotFoundError(f"Actividad {actividad_id} no encontrada")
