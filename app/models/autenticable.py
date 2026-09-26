from abc import ABC, abstractmethod

import bcrypt


class Autenticable(ABC):
    def __init__(self, correo, contraseña_hash):
        self.correo = correo
        self.contraseña_hash = contraseña_hash

    def verificar_contraseña(self, contraseña_ingresada):
        return bcrypt.checkpw(
            contraseña_ingresada.encode("utf-8"),
            self.contraseña_hash.encode("utf-8"),
        )

    @staticmethod
    def hashear_contraseña(contraseña_plana):
        return bcrypt.hashpw(
            contraseña_plana.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    @abstractmethod
    def to_dict(self):
        pass
