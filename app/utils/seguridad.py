from functools import wraps

from flask import request, session

from app.utils.errors import NoAutorizadoError, ProhibidoError


# Defensa contra peticiones falsificadas desde otro sitio (CSRF). La sesión viaja en una cookie, y un
# formulario o una imagen de otra página podría usarla sin que el usuario lo sepa. Por eso toda
# petición que cambia datos debe traer este encabezado: una página de otro origen no puede agregarlo
# sin que el navegador le pida permiso al servidor (CORS), y el servidor no se lo concede.
# Junto con la cookie SameSite=Lax (app/config.py) son las dos medidas que recomienda OWASP para
# una API que solo consume su propia interfaz.
ENCABEZADO_PROPIO = "X-Requested-With"
VALOR_ENCABEZADO_PROPIO = "GestLab"
METODOS_QUE_CAMBIAN_DATOS = ("POST", "PUT", "PATCH", "DELETE")


def exigir_peticion_propia() -> None:
    """Rechaza las peticiones que cambian datos y no vienen de la interfaz de GestLab."""
    if request.method in METODOS_QUE_CAMBIAN_DATOS \
            and request.headers.get(ENCABEZADO_PROPIO) != VALOR_ENCABEZADO_PROPIO:
        raise ProhibidoError("Petición rechazada: no viene de la interfaz de GestLab")


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
