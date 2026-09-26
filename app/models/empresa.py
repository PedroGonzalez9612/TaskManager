from app.models.enums import Rol

# Qué campo de la empresa limita la cantidad de usuarios de cada rol.
CAMPO_LIMITE_POR_ROL = {
    Rol.ADMINISTRADOR.value: "limite_administradores",
    Rol.OPERARIO.value: "limite_operarios",
}


class Empresa:
    def __init__(self, nombre, nit, sector, direccion, limite_administradores, limite_operarios, id=None):
        self.id = id
        self.nombre = nombre
        self.nit = nit
        self.sector = sector
        self.direccion = direccion
        self.limite_administradores = limite_administradores
        self.limite_operarios = limite_operarios

    def to_dict(self):
        return {
            "nombre": self.nombre,
            "nit": self.nit,
            "sector": self.sector,
            "direccion": self.direccion,
            "limite_administradores": self.limite_administradores,
            "limite_operarios": self.limite_operarios,
        }

    @staticmethod
    def from_doc(doc):
        # El logo (la imagen) no viaja en el JSON: se pide aparte en /empresas/<id>/logo.
        return {
            "id": str(doc["_id"]),
            "nombre": doc["nombre"],
            "nit": doc["nit"],
            "sector": doc.get("sector", ""),
            "direccion": doc.get("direccion", ""),
            # None = sin límite (empresas creadas antes de que existieran los límites).
            "limite_administradores": doc.get("limite_administradores"),
            "limite_operarios": doc.get("limite_operarios"),
            "tiene_logo": bool(doc.get("logo_tipo")),
        }
