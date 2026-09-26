from app.models.enums import Rol
from app.models.usuario import Usuario
from app.utils.errors import NoAutorizadoError


class AuthService:
    def __init__(self, usuario_repository):
        self.usuario_repository = usuario_repository

    def iniciar_sesion(self, correo: str, contraseña: str) -> dict:
        correo = (correo or "").strip().lower()
        doc = self.usuario_repository.find_by_correo(correo) if correo else None

        # Mismo mensaje si el correo no existe o si la contraseña falla:
        # así no se revela qué correos están registrados.
        if not doc or not contraseña or not Usuario.desde_documento(doc).verificar_contraseña(contraseña):
            raise NoAutorizadoError("Correo o contraseña incorrectos")
        return Usuario.from_doc(doc)

    def crear_superadmin_inicial(self, nombre: str, correo: str, contraseña: str) -> bool:
        """Crea el Superadmin la primera vez que arranca el sistema. Devuelve True si lo creó."""
        if not correo or not contraseña or self.usuario_repository.existe_rol(Rol.SUPERADMIN.value):
            return False

        superadmin = Usuario(
            nombre=nombre or "Superadmin",
            correo=correo.strip().lower(),
            contraseña_hash=Usuario.hashear_contraseña(contraseña),
            rol=Rol.SUPERADMIN,
        )
        self.usuario_repository.insert(superadmin.to_dict())
        return True
