class ErrorApi(Exception):
    """Error de negocio que se responde al cliente como JSON con su código HTTP."""
    status_code = 500


class ValidationError(ErrorApi):
    status_code = 400


class NoAutorizadoError(ErrorApi):
    """No hay sesión iniciada o las credenciales no son válidas."""
    status_code = 401


class ProhibidoError(ErrorApi):
    """Hay sesión, pero el rol no tiene permiso para esta acción."""
    status_code = 403


class NotFoundError(ErrorApi):
    status_code = 404
