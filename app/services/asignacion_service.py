from app.models.asignacion import Asignacion
from app.models.enums import EstadoActividad
from app.utils.errors import NotFoundError, ValidationError


class AsignacionService:
    def __init__(self, asignacion_repository, actividad_repository, usuario_repository):
        self.asignacion_repository = asignacion_repository
        self.actividad_repository = actividad_repository
        self.usuario_repository = usuario_repository

    def asignar(self, data: dict) -> dict:
        actividad_id = data.get("actividad_id")
        usuario_id = data.get("usuario_id")

        if not actividad_id or not usuario_id:
            raise ValidationError("actividad_id y usuario_id son obligatorios")

        if not self.actividad_repository.find_by_id(actividad_id):
            raise NotFoundError(f"Actividad {actividad_id} no encontrada")

        if not self.usuario_repository.find_by_id(usuario_id):
            raise NotFoundError(f"Usuario {usuario_id} no encontrado")

        existente = self.asignacion_repository.find_by_actividad(actividad_id)
        asignacion = Asignacion(actividad_id=actividad_id, usuario_id=usuario_id)

        if existente:
            self.asignacion_repository.update(str(existente["_id"]), asignacion.to_dict())
            asignacion_id = str(existente["_id"])
        else:
            asignacion_id = self.asignacion_repository.insert(asignacion.to_dict())

        self.actividad_repository.update(actividad_id, {"estado": EstadoActividad.ASIGNADA.value})
        return self.obtener_asignacion(asignacion_id)

    def obtener_asignacion(self, asignacion_id: str) -> dict:
        doc = self.asignacion_repository.find_by_id(asignacion_id)
        if not doc:
            raise NotFoundError(f"Asignación {asignacion_id} no encontrada")
        return Asignacion.from_doc(doc)

    def obtener_por_actividad(self, actividad_id: str) -> dict:
        doc = self.asignacion_repository.find_by_actividad(actividad_id)
        if not doc:
            raise NotFoundError(f"No hay asignación para la actividad {actividad_id}")
        return Asignacion.from_doc(doc)

    def listar_por_usuario(self, usuario_id: str) -> list:
        docs = self.asignacion_repository.find_by_usuario(usuario_id)
        return [Asignacion.from_doc(doc) for doc in docs]

    def eliminar_asignacion(self, asignacion_id: str) -> None:
        deleted = self.asignacion_repository.delete(asignacion_id)
        if not deleted:
            raise NotFoundError(f"Asignación {asignacion_id} no encontrada")
