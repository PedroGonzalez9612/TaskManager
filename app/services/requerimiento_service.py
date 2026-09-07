from app.models.requerimiento import Requerimiento
from app.models.enums import EstadoRequerimiento
from app.utils.errors import NotFoundError, ValidationError


class RequerimientoService:
    def __init__(self, requerimiento_repository, empresa_repository):
        self.requerimiento_repository = requerimiento_repository
        self.empresa_repository = empresa_repository

    def crear_requerimiento(self, data: dict) -> dict:
        titulo = data.get("titulo")
        empresa_id = data.get("empresa_id")
        descripcion = data.get("descripcion", "")

        if not titulo or not empresa_id:
            raise ValidationError("titulo y empresa_id son obligatorios")

        if not self.empresa_repository.find_by_id(empresa_id):
            raise NotFoundError(f"Empresa {empresa_id} no encontrada")

        requerimiento = Requerimiento(titulo=titulo, descripcion=descripcion, empresa_id=empresa_id)
        requerimiento_id = self.requerimiento_repository.insert(requerimiento.to_dict())
        return self.obtener_requerimiento(requerimiento_id)

    def obtener_requerimiento(self, requerimiento_id: str) -> dict:
        doc = self.requerimiento_repository.find_by_id(requerimiento_id)
        if not doc:
            raise NotFoundError(f"Requerimiento {requerimiento_id} no encontrado")
        return Requerimiento.from_doc(doc)

    def listar_requerimientos(self, empresa_id: str = None) -> list:
        docs = self.requerimiento_repository.find_by_empresa(empresa_id) if empresa_id \
            else self.requerimiento_repository.find_all()
        return [Requerimiento.from_doc(doc) for doc in docs]

    def actualizar_requerimiento(self, requerimiento_id: str, data: dict) -> dict:
        updates = {k: v for k, v in data.items() if k in ("titulo", "descripcion", "estado")}
        if "estado" in updates and updates["estado"] not in [e.value for e in EstadoRequerimiento]:
            raise ValidationError(f"estado inválido: {updates['estado']}")
        if not updates:
            raise ValidationError("No hay campos válidos para actualizar")
        updated = self.requerimiento_repository.update(requerimiento_id, updates)
        if not updated:
            raise NotFoundError(f"Requerimiento {requerimiento_id} no encontrado")
        return self.obtener_requerimiento(requerimiento_id)

    def eliminar_requerimiento(self, requerimiento_id: str) -> None:
        deleted = self.requerimiento_repository.delete(requerimiento_id)
        if not deleted:
            raise NotFoundError(f"Requerimiento {requerimiento_id} no encontrado")
