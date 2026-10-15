from app.models.autenticable import Autenticable
from app.models.enums import Rol
from app.utils.errors import ValidationError


class Usuario(Autenticable):
    def __init__(self, nombre, correo, contraseña_hash, rol, empresa_id=None, id=None, activo=True):
        super().__init__(correo, contraseña_hash)
        self.id = id
        self.nombre = nombre
        self.rol = rol
        # El Superadmin no pertenece a ninguna empresa, por eso empresa_id puede ser None.
        self.empresa_id = empresa_id
        # Un usuario no se borra: se desactiva y conserva su nombre y su historial (alcance, Sección 4).
        self.activo = activo

    def desactivar(self) -> None:
        if not self.activo:
            raise ValidationError(f"El usuario de {self.nombre} ya está desactivado")
        self.activo = False

    def reactivar(self) -> None:
        if self.activo:
            raise ValidationError(f"El usuario de {self.nombre} ya está activo")
        self.activo = True

    def to_dict(self):
        return {
            "nombre": self.nombre,
            "correo": self.correo,
            "contraseña_hash": self.contraseña_hash,
            "rol": self.rol.value if isinstance(self.rol, Rol) else self.rol,
            "empresa_id": self.empresa_id,
            "activo": self.activo,
        }

    @classmethod
    def desde_documento(cls, doc):
        """Reconstruye el objeto completo (con hash) para poder verificar la contraseña."""
        return cls(
            nombre=doc["nombre"],
            correo=doc["correo"],
            contraseña_hash=doc["contraseña_hash"],
            rol=Rol(doc["rol"]),
            empresa_id=doc.get("empresa_id"),
            id=str(doc["_id"]),
            # Los usuarios anteriores a esta regla no tienen el campo: están activos.
            activo=doc.get("activo", True),
        )

    @staticmethod
    def from_doc(doc):
        """Datos públicos del usuario: nunca incluye el hash de la contraseña."""
        return {
            "id": str(doc["_id"]),
            "nombre": doc["nombre"],
            "correo": doc["correo"],
            "rol": doc["rol"],
            "empresa_id": doc.get("empresa_id"),
            "activo": doc.get("activo", True),
        }
