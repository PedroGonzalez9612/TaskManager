from functools import wraps

from flask import session

from app.utils.errors import NoAutorizadoError, ProhibidoError


def guardar_sesion(usuario: dict) -> None:
    session.clear()
    session["usuario"] = {
        "id": usuario["id"],
        "nombre": usuario["nombre"],
        "rol": usuario["rol"],
        "empresa_id": usuario["empresa_id"],
    }


def usuario_actual():
    return session.get("usuario")


def requiere_rol(*roles):
    """Protege una ruta: exige sesión iniciada y, si se indican roles, que el usuario tenga uno de ellos."""
    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            usuario = usuario_actual()
            if not usuario:
                raise NoAutorizadoError("Debes iniciar sesión")
            if roles and usuario["rol"] not in [rol.value for rol in roles]:
                raise ProhibidoError("No tienes permiso para esta acción")
            return funcion(*args, **kwargs)
        return envoltura
    return decorador
