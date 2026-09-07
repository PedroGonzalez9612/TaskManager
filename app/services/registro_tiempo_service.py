from app.models.registro_tiempo import RegistroTiempo
from app.utils.errors import NotFoundError, ValidationError


class RegistroTiempoService:
    def __init__(self, registro_tiempo_repository, actividad_repository, usuario_repository):
        self.registro_tiempo_repository = registro_tiempo_repository
        self.actividad_repository = actividad_repository
        self.usuario_repository = usuario_repository

    def registrar_tiempo(self, data: dict) -> dict:
        actividad_id = data.get("actividad_id")
        usuario_id = data.get("usuario_id")
        horas = data.get("horas")
        descripcion = data.get("descripcion", "")

        if not actividad_id or not usuario_id or horas is None:
            raise ValidationError("actividad_id, usuario_id y horas son obligatorios")

        try:
            horas = float(horas)
        except (TypeError, ValueError):
            raise ValidationError("horas debe ser un número")

        if horas <= 0:
            raise ValidationError("horas debe ser mayor que 0")

        if not self.actividad_repository.find_by_id(actividad_id):
            raise NotFoundError(f"Actividad {actividad_id} no encontrada")

        if not self.usuario_repository.find_by_id(usuario_id):
            raise NotFoundError(f"Usuario {usuario_id} no encontrado")

        registro = RegistroTiempo(
            actividad_id=actividad_id, usuario_id=usuario_id, horas=horas, descripcion=descripcion
        )
        registro_id = self.registro_tiempo_repository.insert(registro.to_dict())
        return self.obtener_registro(registro_id)

    def obtener_registro(self, registro_id: str) -> dict:
        doc = self.registro_tiempo_repository.find_by_id(registro_id)
        if not doc:
            raise NotFoundError(f"Registro de tiempo {registro_id} no encontrado")
        return RegistroTiempo.from_doc(doc)

    def listar_por_actividad(self, actividad_id: str) -> list:
        docs = self.registro_tiempo_repository.find_by_actividad(actividad_id)
        return [RegistroTiempo.from_doc(doc) for doc in docs]

    def listar_por_usuario(self, usuario_id: str) -> list:
        docs = self.registro_tiempo_repository.find_by_usuario(usuario_id)
        return [RegistroTiempo.from_doc(doc) for doc in docs]

    def eliminar_registro(self, registro_id: str) -> None:
        deleted = self.registro_tiempo_repository.delete(registro_id)
        if not deleted:
            raise NotFoundError(f"Registro de tiempo {registro_id} no encontrado")
