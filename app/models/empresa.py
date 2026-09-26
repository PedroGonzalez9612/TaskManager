class Empresa:
    def __init__(self, nombre, nit, sector, direccion, id=None):
        self.id = id
        self.nombre = nombre
        self.nit = nit
        self.sector = sector
        self.direccion = direccion

    def to_dict(self):
        return {
            "nombre": self.nombre,
            "nit": self.nit,
            "sector": self.sector,
            "direccion": self.direccion,
        }

    @staticmethod
    def from_doc(doc):
        return {
            "id": str(doc["_id"]),
            "nombre": doc["nombre"],
            "nit": doc["nit"],
            "sector": doc.get("sector", ""),
            "direccion": doc.get("direccion", ""),
        }
