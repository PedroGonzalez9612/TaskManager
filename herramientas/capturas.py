"""Toma capturas de las pantallas de GestLab para revisar el diseño.

Recorre las pantallas listadas en herramientas/pantallas.json, inicia sesión
con un usuario de prueba de cada rol y guarda cada pantalla en tamaño celular
y escritorio. Por cada captura genera además dos versiones de apoyo:

- _desenfoque: prueba del desenfoque (squint test) para revisar la jerarquía
  visual; lo que se sigue distinguiendo es lo que domina la pantalla.
- _grises: escala de grises para comprobar que la jerarquía y los estados se
  entienden sin color (regla "color, ícono y texto" de la Sección 6.3).

Las credenciales de prueba se leen del archivo .env (nunca del código):
    CAPTURAS_URL=http://localhost:5000
    CAPTURAS_SUPERADMIN_CORREO=...      CAPTURAS_SUPERADMIN_CONTRASENA=...
    CAPTURAS_ADMINISTRADOR_CORREO=...   CAPTURAS_ADMINISTRADOR_CONTRASENA=...
    CAPTURAS_OPERARIO_CORREO=...        CAPTURAS_OPERARIO_CONTRASENA=...
Si faltan las del Superadmin, se usan SUPERADMIN_CORREO y SUPERADMIN_CONTRASENA.

Requisitos (solo para desarrollo): pip install -r requirements-dev.txt

Navegador: se puede usar uno basado en Chromium que ya esté instalado (Brave, Edge,
Chrome) indicando su ejecutable en CAPTURAS_NAVEGADOR del .env o con --navegador.
Si no se indica ninguno, se usa el Chromium de Playwright, que hay que descargar
una vez con: python -m playwright install chromium

Uso, con la aplicación corriendo:
    python herramientas/capturas.py
    python herramientas/capturas.py --rol operario
    python herramientas/capturas.py --pantalla usuarios
    python herramientas/capturas.py --navegador "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageFilter, ImageOps
from playwright.sync_api import Error as ErrorPlaywright
from playwright.sync_api import sync_playwright

RUTA_PANTALLAS = Path("herramientas/pantallas.json")
CARPETA_SALIDA = Path("herramientas/capturas")

# Tamaños de pantalla: celular común (persona Carlos) y escritorio (Administrador, Superadmin).
VISTAS = {
    "movil": {"width": 390, "height": 844},
    "escritorio": {"width": 1440, "height": 900},
}

RADIO_DESENFOQUE = 6
TIEMPO_ESPERA_MS = 15000


def leer_pantallas(ruta, rol=None, nombre=None):
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    pantallas = datos["pantallas"]
    if rol:
        pantallas = [p for p in pantallas if p["rol"] == rol]
    if nombre:
        pantallas = [p for p in pantallas if p["nombre"] == nombre]
    return pantallas


def credenciales_de(rol):
    """Devuelve (correo, contraseña) del rol, o None si no están en el .env."""
    clave = rol.upper()
    correo = os.getenv(f"CAPTURAS_{clave}_CORREO")
    contrasena = os.getenv(f"CAPTURAS_{clave}_CONTRASENA")
    if rol == "superadmin" and not (correo and contrasena):
        correo = os.getenv("SUPERADMIN_CORREO")
        contrasena = os.getenv("SUPERADMIN_CONTRASENA")
    if correo and contrasena:
        return correo, contrasena
    return None


def iniciar_sesion(contexto, url_base, credenciales):
    """Inicia sesión por la API; la cookie de sesión queda en el contexto del navegador."""
    correo, contrasena = credenciales
    respuesta = contexto.request.post(
        f"{url_base}/auth/login",
        data={"correo": correo, "contraseña": contrasena},
    )
    if not respuesta.ok:
        raise RuntimeError(f"El inicio de sesión respondió {respuesta.status}.")


def abrir_pantalla(pagina, url_base, pantalla):
    """Navega a la pantalla, directo por su ruta o desde otra pantalla con un clic."""
    if "ruta" in pantalla:
        pagina.goto(f"{url_base}{pantalla['ruta']}", wait_until="networkidle")
    else:
        pagina.goto(f"{url_base}{pantalla['desde']}", wait_until="networkidle")
        pagina.locator(pantalla["clic"]).first.click(timeout=TIEMPO_ESPERA_MS)
        pagina.wait_for_load_state("networkidle")
    if "esperar" in pantalla:
        pagina.wait_for_selector(pantalla["esperar"], timeout=TIEMPO_ESPERA_MS)


def generar_variantes(ruta_png):
    """Crea la versión desenfocada y la versión en escala de grises de una captura."""
    with Image.open(ruta_png) as imagen:
        imagen = imagen.convert("RGB")
        desenfoque = ruta_png.with_name(ruta_png.stem + "_desenfoque.png")
        grises = ruta_png.with_name(ruta_png.stem + "_grises.png")
        imagen.filter(ImageFilter.GaussianBlur(RADIO_DESENFOQUE)).save(desenfoque)
        ImageOps.grayscale(imagen).save(grises)
    return desenfoque, grises


def capturar_rol(navegador, url_base, rol, pantallas, carpeta, indice):
    credenciales = credenciales_de(rol) if rol != "publico" else None
    if rol != "publico" and credenciales is None:
        aviso = f"Sin credenciales en .env para el rol {rol}; se omiten sus pantallas."
        print(f"AVISO: {aviso}")
        indice["avisos"].append(aviso)
        return

    for nombre_vista, tamano in VISTAS.items():
        contexto = navegador.new_context(viewport=tamano, locale="es-CO")
        try:
            if credenciales:
                iniciar_sesion(contexto, url_base, credenciales)
            pagina = contexto.new_page()
            for pantalla in pantallas:
                registrar_captura(pagina, url_base, rol, pantalla, nombre_vista, carpeta, indice)
        except (RuntimeError, ErrorPlaywright) as error:
            aviso = f"Rol {rol}, vista {nombre_vista}: {error}"
            print(f"AVISO: {aviso}")
            indice["avisos"].append(aviso)
        finally:
            contexto.close()


def registrar_captura(pagina, url_base, rol, pantalla, nombre_vista, carpeta, indice):
    nombre_archivo = f"{rol}_{pantalla['nombre']}_{nombre_vista}.png"
    ruta_png = carpeta / nombre_archivo
    try:
        abrir_pantalla(pagina, url_base, pantalla)
        pagina.screenshot(path=str(ruta_png), full_page=True)
    except ErrorPlaywright as error:
        aviso = f"No se pudo capturar {rol}/{pantalla['nombre']} ({nombre_vista}): {error.message.splitlines()[0]}"
        print(f"AVISO: {aviso}")
        indice["avisos"].append(aviso)
        return
    desenfoque, grises = generar_variantes(ruta_png)
    indice["capturas"].append({
        "rol": rol,
        "pantalla": pantalla["nombre"],
        "vista": nombre_vista,
        "url": pagina.url,
        "captura": str(ruta_png),
        "desenfoque": str(desenfoque),
        "grises": str(grises),
    })
    print(f"OK  {nombre_archivo}")


def crear_parser():
    parser = argparse.ArgumentParser(description="Capturas de las pantallas de GestLab para revisar el diseño.")
    parser.add_argument("--rol", choices=["publico", "superadmin", "administrador", "operario"],
                        help="Capturar solo las pantallas de un rol.")
    parser.add_argument("--pantalla", help="Capturar solo la pantalla con este nombre (ver pantallas.json).")
    parser.add_argument("--url", help="Dirección de la aplicación (por defecto CAPTURAS_URL o http://localhost:5000).")
    parser.add_argument("--navegador", help="Ejecutable de un navegador Chromium ya instalado, como Brave o Edge "
                                            "(por defecto CAPTURAS_NAVEGADOR o el Chromium de Playwright).")
    return parser


def abrir_navegador(playwright, ejecutable):
    """Abre el navegador indicado o, si no se indicó ninguno, el Chromium de Playwright."""
    if ejecutable and not Path(ejecutable).is_file():
        raise RuntimeError(f"No existe el navegador indicado: {ejecutable}")
    try:
        return playwright.chromium.launch(executable_path=ejecutable or None)
    except ErrorPlaywright as error:
        raise RuntimeError(
            f"No se pudo abrir el navegador ({error.message.splitlines()[0]}). Indica uno instalado con "
            "CAPTURAS_NAVEGADOR o --navegador, o descarga Chromium con 'python -m playwright install chromium'."
        )


def main(argumentos=None):
    args = crear_parser().parse_args(argumentos)
    load_dotenv()
    url_base = (args.url or os.getenv("CAPTURAS_URL", "http://localhost:5000")).rstrip("/")
    pantallas = leer_pantallas(RUTA_PANTALLAS, args.rol, args.pantalla)
    if not pantallas:
        print("No hay pantallas que coincidan con el filtro.", file=sys.stderr)
        return 2

    carpeta = CARPETA_SALIDA / datetime.now().strftime("%Y-%m-%d_%H%M")
    carpeta.mkdir(parents=True, exist_ok=True)
    indice = {"fecha": datetime.now().isoformat(timespec="seconds"), "url": url_base,
              "vistas": VISTAS, "capturas": [], "avisos": []}

    roles = list(dict.fromkeys(p["rol"] for p in pantallas))
    with sync_playwright() as playwright:
        try:
            navegador = abrir_navegador(playwright, args.navegador or os.getenv("CAPTURAS_NAVEGADOR"))
        except RuntimeError as error:
            print(f"Error: {error}", file=sys.stderr)
            return 2
        try:
            for rol in roles:
                del_rol = [p for p in pantallas if p["rol"] == rol]
                capturar_rol(navegador, url_base, rol, del_rol, carpeta, indice)
        finally:
            navegador.close()

    (carpeta / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(indice['capturas'])} capturas en {carpeta} (índice: {carpeta / 'indice.json'})")
    return 0 if indice["capturas"] and not indice["avisos"] else 1


if __name__ == "__main__":
    sys.exit(main())
