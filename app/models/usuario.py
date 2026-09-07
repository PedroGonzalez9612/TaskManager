class Usuario:
    def __init__(self, nombre, email, empresa_id, rol="MIEMBRO", id=None):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.empresa_id = empresa_id
        self.rol = rol

    def to_dict(self):
        return {
            "nombre": self.nombre,
            "email": self.email,
            "empresa_id": self.empresa_id,
            "rol": self.rol,
        }

    @staticmethod
    def from_doc(doc):
        return {
            "id": str(doc["_id"]),
            "nombre": doc["nombre"],
            "email": doc["email"],
            "empresa_id": doc["empresa_id"],
            "rol": doc.get("rol", "MIEMBRO"),
        }
