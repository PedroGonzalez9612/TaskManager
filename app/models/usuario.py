from app.models.autenticable import Autenticable
from app.models.enums import Rol


class Usuario(Autenticable):
    def __init__(self, nombre, correo, contraseña_hash, rol, empresa_id=None, id=None):
        super().__init__(correo, contraseña_hash)
        self.id = id
        self.nombre = nombre
        self.rol = rol
        # El Superadmin no pertenece a ninguna empresa, por eso empresa_id puede ser None.
        self.empresa_id = empresa_id

    def to_dict(self):
        return {
            "nombre": self.nombre,
            "correo": self.correo,
            "contraseña_hash": self.contraseña_hash,
            "rol": self.rol.value if isinstance(self.rol, Rol) else self.rol,
            "empresa_id": self.empresa_id,
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
        }
