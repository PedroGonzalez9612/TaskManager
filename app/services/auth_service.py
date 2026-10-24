from app.models.enums import Rol
from app.models.usuario import Usuario
from app.services.usuario_service import LONGITUD_MINIMA_CONTRASEÑA
from app.utils.errors import NoAutorizadoError, NotFoundError, ValidationError


class AuthService:
    def __init__(self, usuario_repository, empresa_repository=None):
        self.usuario_repository = usuario_repository
        # Para no dejar entrar a los usuarios de una empresa desactivada.
        self.empresa_repository = empresa_repository

    def iniciar_sesion(self, correo: str, contraseña: str) -> dict:
        correo = (correo or "").strip().lower()
        doc = self.usuario_repository.find_by_correo(correo) if correo else None

        # Mismo mensaje si el correo no existe o si la contraseña falla:
        # así no se revela qué correos están registrados.
        if not doc or not contraseña or not Usuario.desde_documento(doc).verificar_contraseña(contraseña):
            raise NoAutorizadoError("Correo o contraseña incorrectos")
        # Solo después de comprobar la contraseña: así no se revela si un correo está desactivado.
        if doc.get("activo") is False:
            raise NoAutorizadoError("Tu usuario está desactivado. Habla con el Administrador de tu empresa.")
        empresa = self.empresa_repository.find_by_id(doc["empresa_id"]) \
            if self.empresa_repository is not None and doc.get("empresa_id") else None
        if empresa and empresa.get("activa") is False:
            raise NoAutorizadoError("Tu empresa está desactivada en GestLab.")
        return Usuario.from_doc(doc)

    def cambiar_contraseña(self, solicitante: dict, actual: str, nueva: str) -> None:
        """Mi perfil (alcance, Sección 5.1): el usuario cambia su propia contraseña escribiendo la
        actual. La nueva tiene la misma longitud mínima que al crear un usuario y es distinta."""
        doc = self.usuario_repository.find_by_id(solicitante["id"])
        if not doc:
            raise NotFoundError("Tu usuario ya no existe")
        usuario = Usuario.desde_documento(doc)
        if not actual or not usuario.verificar_contraseña(actual):
            raise ValidationError("La contraseña actual no es correcta")
        nueva = nueva or ""
        if len(nueva) < LONGITUD_MINIMA_CONTRASEÑA:
            raise ValidationError(f"La contraseña nueva debe tener al menos {LONGITUD_MINIMA_CONTRASEÑA} caracteres")
        if nueva == actual:
            raise ValidationError("La contraseña nueva debe ser distinta de la actual")
        self.usuario_repository.update(solicitante["id"], {"contraseña_hash": Usuario.hashear_contraseña(nueva)})

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
