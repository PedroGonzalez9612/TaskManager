class NotFoundError(Exception):
    status_code = 404


class ValidationError(Exception):
    status_code = 400
