from app.models.usuario import Usuario
from app.utils.errors import NotFoundError, ValidationError


class UsuarioService:
    def __init__(self, usuario_repository, empresa_repository):
        self.usuario_repository = usuario_repository
        self.empresa_repository = empresa_repository

    def crear_usuario(self, data: dict) -> dict:
        nombre = data.get("nombre")
        email = data.get("email")
        empresa_id = data.get("empresa_id")
        rol = data.get("rol", "MIEMBRO")

        if not nombre or not email or not empresa_id:
            raise ValidationError("nombre, email y empresa_id son obligatorios")

        if not self.empresa_repository.find_by_id(empresa_id):
            raise NotFoundError(f"Empresa {empresa_id} no encontrada")

        if self.usuario_repository.find_by_email(email):
            raise ValidationError(f"Ya existe un usuario con email {email}")

        usuario = Usuario(nombre=nombre, email=email, empresa_id=empresa_id, rol=rol)
        usuario_id = self.usuario_repository.insert(usuario.to_dict())
        return self.obtener_usuario(usuario_id)

    def obtener_usuario(self, usuario_id: str) -> dict:
        doc = self.usuario_repository.find_by_id(usuario_id)
        if not doc:
            raise NotFoundError(f"Usuario {usuario_id} no encontrado")
        return Usuario.from_doc(doc)

    def listar_usuarios(self, empresa_id: str = None) -> list:
        docs = self.usuario_repository.find_by_empresa(empresa_id) if empresa_id \
            else self.usuario_repository.find_all()
        return [Usuario.from_doc(doc) for doc in docs]

    def actualizar_usuario(self, usuario_id: str, data: dict) -> dict:
        updates = {k: v for k, v in data.items() if k in ("nombre", "email", "rol")}
        if not updates:
            raise ValidationError("No hay campos válidos para actualizar")
        updated = self.usuario_repository.update(usuario_id, updates)
        if not updated:
            raise NotFoundError(f"Usuario {usuario_id} no encontrado")
        return self.obtener_usuario(usuario_id)

    def eliminar_usuario(self, usuario_id: str) -> None:
        deleted = self.usuario_repository.delete(usuario_id)
        if not deleted:
            raise NotFoundError(f"Usuario {usuario_id} no encontrado")
