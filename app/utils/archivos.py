"""Reconocer el tipo real de un archivo subido por sus primeros bytes, no por su nombre ni por lo
que diga el navegador: ambos se pueden falsificar. Lo usan el logo de la empresa y la evidencia
de la ejecución."""

PDF = "application/pdf"


def detectar_tipo_imagen(contenido: bytes):
    """PNG, JPG o WEBP. No se aceptan SVG porque pueden contener código."""
    if contenido.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if contenido.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP":
        return "image/webp"
    return None


def detectar_tipo_documento(contenido: bytes):
    """Una imagen de las anteriores o un PDF. None si no es ninguno."""
    if contenido.startswith(b"%PDF-"):
        return PDF
    return detectar_tipo_imagen(contenido)


def es_imagen(tipo: str) -> bool:
    return bool(tipo) and tipo.startswith("image/")
