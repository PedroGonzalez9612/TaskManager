class Empresa:
    def __init__(self, nombre, nit, id=None):
        self.id = id
        self.nombre = nombre
        self.nit = nit

    def to_dict(self):
        return {"nombre": self.nombre, "nit": self.nit}

    @staticmethod
    def from_doc(doc):
        return {
            "id": str(doc["_id"]),
            "nombre": doc["nombre"],
            "nit": doc["nit"],
        }
