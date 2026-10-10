"""La hora del servidor y el día que es para cada empresa.

Todos los eventos se guardan en UTC. Pero "hoy" depende de dónde está la empresa: a las 8 de la
noche en Bogotá ya es el día siguiente en UTC. Por eso cada empresa tiene su zona horaria (alcance,
Sección 5.1) y con ella se decide a qué día pertenece un momento y cuándo termina una jornada."""
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.utils.errors import ValidationError

ZONA_POR_DEFECTO = "America/Bogota"
FORMATO_FECHA = "%Y-%m-%d"


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


def validar_zona(nombre) -> str:
    """Devuelve el nombre de la zona si existe (por ejemplo "America/Bogota")."""
    nombre = (nombre or "").strip()
    try:
        ZoneInfo(nombre)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        raise ValidationError(f'La zona horaria "{nombre}" no existe. Ejemplo válido: {ZONA_POR_DEFECTO}')
    return nombre


def _zona(nombre) -> ZoneInfo:
    return ZoneInfo(nombre or ZONA_POR_DEFECTO)


def fecha_local(momento: datetime, zona=None) -> str:
    """El día ("AAAA-MM-DD") que es en esa zona en ese momento. Una fecha sin zona se toma como UTC."""
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(_zona(zona)).strftime(FORMATO_FECHA)


def momento_local(fecha: str, hora: str, zona=None) -> datetime:
    """El momento (en UTC) que corresponde a esa fecha ("AAAA-MM-DD") y esa hora ("HH:MM") en esa zona."""
    local = datetime.strptime(f"{fecha} {hora}", f"{FORMATO_FECHA} %H:%M").replace(tzinfo=_zona(zona))
    return local.astimezone(timezone.utc)


def fin_del_dia(fecha: str, zona=None) -> datetime:
    """El momento (en UTC) en que termina ese día en esa zona: la medianoche con que empieza el siguiente."""
    siguiente = datetime.strptime(fecha, FORMATO_FECHA).date() + timedelta(days=1)
    return datetime.combine(siguiente, time.min, tzinfo=_zona(zona)).astimezone(timezone.utc)
