"""Calcula la relación de contraste WCAG 2.1 entre pares de colores.

Herramienta de apoyo para revisar el sistema de color de GestLab
(Sección 6.3 de docs/alcance_proyecto.md). Solo usa la biblioteca estándar.

Cada color puede escribirse como HEX (#16697A, #FFF) o como el nombre de una
variable CSS definida en :root de app/static/css/estilos.css, sin los guiones
iniciales (por ejemplo: texto, superficie).

Ejemplos:
    python herramientas/contraste.py "#1F2A2E" "#FFFFFF"
    python herramientas/contraste.py texto fondo principal superficie
    python herramientas/contraste.py texto fondo --minimo 7
    python herramientas/contraste.py texto fondo --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

RUTA_CSS_POR_DEFECTO = Path("app/static/css/estilos.css")

# Umbrales de WCAG 2.1 (criterios 1.4.3, 1.4.6 y 1.4.11).
UMBRALES = {
    "aa_texto_normal": 4.5,
    "aa_texto_grande": 3.0,
    "aaa_texto_normal": 7.0,
    "aaa_texto_grande": 4.5,
    "componentes_interfaz": 3.0,
}

PATRON_HEX = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
PATRON_VARIABLE = re.compile(r"--([\w-]+)\s*:\s*([^;]+);")
PATRON_REFERENCIA = re.compile(r"^var\(\s*--([\w-]+)\s*(?:,[^)]*)?\)$")


class ErrorColor(ValueError):
    """Color que no se puede interpretar o resolver."""


def leer_variables_css(ruta_css):
    """Devuelve las variables definidas en el primer bloque :root del CSS."""
    if not ruta_css.exists():
        return {}
    contenido = ruta_css.read_text(encoding="utf-8")
    contenido = re.sub(r"/\*.*?\*/", "", contenido, flags=re.DOTALL)
    bloque = re.search(r":root\s*\{(.*?)\}", contenido, flags=re.DOTALL)
    if not bloque:
        return {}
    return {nombre: valor.strip() for nombre, valor in PATRON_VARIABLE.findall(bloque.group(1))}


def resolver_color(texto, variables, profundidad=0):
    """Convierte un HEX o un nombre de variable en un HEX de 6 dígitos."""
    if profundidad > 10:
        raise ErrorColor(f"Referencia circular de variables al resolver '{texto}'.")
    texto = texto.strip()
    if PATRON_HEX.match(texto):
        digitos = texto[1:]
        if len(digitos) == 3:
            digitos = "".join(c * 2 for c in digitos)
        return "#" + digitos.upper()
    referencia = PATRON_REFERENCIA.match(texto)
    nombre = referencia.group(1) if referencia else texto.lstrip("-")
    if nombre in variables:
        return resolver_color(variables[nombre], variables, profundidad + 1)
    raise ErrorColor(
        f"No se reconoce '{texto}': no es un HEX válido ni una variable de :root. "
        "Los colores con transparencia (rgba, #RRGGBBAA) no se evalúan porque su "
        "contraste depende del fondo que tengan detrás."
    )


def luminancia_relativa(color_hex):
    """Luminancia relativa según la definición de WCAG 2.1."""
    canales = [int(color_hex[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lineales = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
    rojo, verde, azul = lineales
    return 0.2126 * rojo + 0.7152 * verde + 0.0722 * azul


def relacion_contraste(color_a, color_b):
    """Relación de contraste entre dos HEX, de 1 a 21."""
    clara, oscura = sorted((luminancia_relativa(color_a), luminancia_relativa(color_b)), reverse=True)
    return (clara + 0.05) / (oscura + 0.05)


def evaluar_par(entrada_a, entrada_b, variables, minimo):
    color_a = resolver_color(entrada_a, variables)
    color_b = resolver_color(entrada_b, variables)
    relacion = round(relacion_contraste(color_a, color_b), 2)
    return {
        "color_a": entrada_a,
        "hex_a": color_a,
        "color_b": entrada_b,
        "hex_b": color_b,
        "relacion": relacion,
        "cumple": {nivel: relacion >= umbral for nivel, umbral in UMBRALES.items()},
        "minimo_exigido": minimo,
        "cumple_minimo": relacion >= minimo,
    }


def marca(cumple):
    return "sí" if cumple else "NO"


def imprimir_resultado(resultado):
    cumple = resultado["cumple"]
    print(f"{resultado['color_a']} ({resultado['hex_a']}) sobre {resultado['color_b']} ({resultado['hex_b']})")
    print(f"  Relación de contraste: {resultado['relacion']}:1")
    print(f"  AA texto normal (4,5): {marca(cumple['aa_texto_normal'])} | "
          f"AA texto grande (3): {marca(cumple['aa_texto_grande'])} | "
          f"AAA texto normal (7): {marca(cumple['aaa_texto_normal'])} | "
          f"Componentes (3): {marca(cumple['componentes_interfaz'])}")
    estado = "CUMPLE" if resultado["cumple_minimo"] else "NO CUMPLE"
    print(f"  Mínimo exigido {resultado['minimo_exigido']}:1 -> {estado}\n")


def crear_parser():
    parser = argparse.ArgumentParser(
        description="Relación de contraste WCAG 2.1 entre pares de colores (HEX o variables de :root).")
    parser.add_argument("colores", nargs="+",
                        help="Colores en pares: texto1 fondo1 [texto2 fondo2 ...].")
    parser.add_argument("--css", type=Path, default=RUTA_CSS_POR_DEFECTO,
                        help=f"Archivo CSS con las variables (por defecto {RUTA_CSS_POR_DEFECTO}).")
    parser.add_argument("--minimo", type=float, default=4.5,
                        help="Relación mínima exigida (por defecto 4,5; usar 3 para texto grande o componentes).")
    parser.add_argument("--json", action="store_true", help="Devuelve el resultado en JSON.")
    return parser


def main(argumentos=None):
    args = crear_parser().parse_args(argumentos)
    if len(args.colores) % 2 != 0:
        print("Error: los colores deben ir en pares (texto y fondo).", file=sys.stderr)
        return 2
    variables = leer_variables_css(args.css)
    pares = zip(args.colores[0::2], args.colores[1::2])
    try:
        resultados = [evaluar_par(a, b, variables, args.minimo) for a, b in pares]
    except ErrorColor as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(resultados, ensure_ascii=False, indent=2))
    else:
        for resultado in resultados:
            imprimir_resultado(resultado)
    return 0 if all(r["cumple_minimo"] for r in resultados) else 1


if __name__ == "__main__":
    sys.exit(main())
