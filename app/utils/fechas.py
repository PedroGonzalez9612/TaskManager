from datetime import datetime

from app.utils.errors import ValidationError

FORMATO_FECHA = "%Y-%m-%d"
FORMATO_HORA = "%H:%M"


def validar_fecha(texto, campo: str = "La fecha") -> str:
    """Comprueba que el texto sea una fecha "AAAA-MM-DD" real y lo devuelve normalizado."""
    try:
        return datetime.strptime(str(texto), FORMATO_FECHA).strftime(FORMATO_FECHA)
    except ValueError:
        raise ValidationError(f"{campo} debe tener el formato AAAA-MM-DD")


def validar_hora(texto, campo: str = "La hora") -> str:
    """Comprueba que el texto sea una hora "HH:MM" real y lo devuelve normalizado."""
    try:
        return datetime.strptime(str(texto), FORMATO_HORA).strftime(FORMATO_HORA)
    except ValueError:
        raise ValidationError(f"{campo} debe tener el formato HH:MM")
