from app.models.empresa import Empresa
from app.utils.errors import NotFoundError, ValidationError


class EmpresaService:
    def __init__(self, empresa_repository):
        self.empresa_repository = empresa_repository

    def crear_empresa(self, data: dict) -> dict:
        nombre = data.get("nombre")
        nit = data.get("nit")
        sector = data.get("sector")
        direccion = data.get("direccion")
        if not nombre or not nit or not sector or not direccion:
            raise ValidationError(
                "nombre, nit, sector y direccion son obligatorios"
            )

        empresa = Empresa(nombre=nombre, nit=nit, sector=sector, direccion=direccion)
        empresa_id = self.empresa_repository.insert(empresa.to_dict())
        return self.obtener_empresa(empresa_id)

    def obtener_empresa(self, empresa_id: str) -> dict:
        doc = self.empresa_repository.find_by_id(empresa_id)
        if not doc:
            raise NotFoundError(f"Empresa {empresa_id} no encontrada")
        return Empresa.from_doc(doc)

    def listar_empresas(self) -> list:
        docs = self.empresa_repository.find_all()
        return [Empresa.from_doc(doc) for doc in docs]

    def actualizar_empresa(self, empresa_id: str, data: dict) -> dict:
        updates = {k: v for k, v in data.items() if k in ("nombre", "nit")}
        if not updates:
            raise ValidationError("No hay campos válidos para actualizar")
        updated = self.empresa_repository.update(empresa_id, updates)
        if not updated:
            raise NotFoundError(f"Empresa {empresa_id} no encontrada")
        return self.obtener_empresa(empresa_id)

    def eliminar_empresa(self, empresa_id: str) -> None:
        deleted = self.empresa_repository.delete(empresa_id)
        if not deleted:
            raise NotFoundError(f"Empresa {empresa_id} no encontrada")
