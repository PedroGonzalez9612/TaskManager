"""Convierte un documento Markdown de docs/ en un PDF para entregar.

Pasa el Markdown a HTML, le aplica una hoja de estilos de documento y lo imprime a PDF con el
mismo navegador de las capturas (CAPTURAS_NAVEGADOR del .env, o el Chromium de Playwright).
Los diagramas escritos en bloques ```mermaid se dibujan con la biblioteca Mermaid, que se descarga
de internet en el momento de generar el PDF; sin conexión, el diagrama queda como texto.

Requisitos (solo para desarrollo): pip install -r requirements-dev.txt

Uso, desde la raíz del proyecto:
    python herramientas/documento_pdf.py docs/diseno_interfaces/momento_2/documento_diseno.md
"""

import argparse
import os
import re
import sys
from pathlib import Path

import markdown
from dotenv import load_dotenv
from playwright.sync_api import Error as ErrorPlaywright
from playwright.sync_api import sync_playwright

MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"
TIEMPO_ESPERA_MS = 20000

ESTILOS = """
@page { size: Letter; margin: 2cm 2cm 2.2cm; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10.5pt; line-height: 1.5; color: #1F2A2E; }
h1, h2, h3 { color: #16697A; line-height: 1.25; break-after: avoid; }
h1 { font-size: 22pt; margin: 0 0 6pt; }
h2 { font-size: 15pt; margin: 22pt 0 6pt; padding-bottom: 3pt; border-bottom: 1px solid #E1E5E3; }
h3 { font-size: 12pt; margin: 16pt 0 4pt; }
h4 { font-size: 10.5pt; margin: 12pt 0 2pt; font-family: Consolas, monospace; break-after: avoid; }
p, ul, ol { margin: 0 0 7pt; }
li { margin-bottom: 2pt; }
a { color: #16697A; }
code { font-family: Consolas, monospace; font-size: 9pt; background: #F4F6F5; padding: 0 2pt; border-radius: 2pt; }
pre { background: #F4F6F5; padding: 8pt; border-radius: 4pt; font-size: 8.5pt; white-space: pre-wrap; break-inside: avoid; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt; font-size: 9.5pt; break-inside: auto; }
th, td { border: 1px solid #E1E5E3; padding: 4pt 6pt; text-align: left; vertical-align: top; }
th { background: #E0EFF0; font-weight: 600; }
tr { break-inside: avoid; }
blockquote { margin: 0 0 7pt; padding-left: 10pt; border-left: 3px solid #E1E5E3; color: #5B6664; }
figure { margin: 8pt 0 12pt; text-align: center; break-inside: avoid; }
figcaption { margin-top: 4pt; font-size: 8.5pt; color: #5B6664; }
img { max-width: 100%; border: 1px solid #E1E5E3; border-radius: 4pt; }
img.movil { width: 4.4cm; }
img.recorte { height: 9.5cm; object-fit: cover; object-position: top; }
img.escritorio { width: 15cm; }
img.escritorio-medio { width: 8.2cm; }
.figuras { display: flex; flex-wrap: wrap; justify-content: center; align-items: flex-start; gap: 10pt; break-inside: avoid; }
.figuras figure { margin: 4pt 0 10pt; max-width: 8.4cm; }
.figuras figure:has(img.movil) { max-width: 4.6cm; }
.portada { height: 23cm; display: flex; flex-direction: column; justify-content: center; text-align: center; break-after: page; }
.portada h1 { font-size: 34pt; }
.portada h2 { border: none; font-size: 18pt; color: #1F2A2E; margin: 0 0 28pt; }
.portada p { margin-bottom: 12pt; }
pre.mermaid { background: none; text-align: center; }
"""


def a_html(texto, titulo):
    """El HTML completo del documento, con los bloques mermaid listos para dibujarse."""
    cuerpo = markdown.markdown(texto, extensions=["tables", "fenced_code", "md_in_html", "sane_lists"])
    # fenced_code deja los diagramas como <pre><code class="language-mermaid">; Mermaid espera <pre class="mermaid">.
    cuerpo, diagramas = re.subn(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>', r'<pre class="mermaid">\1</pre>', cuerpo, flags=re.S)
    guion = f'<script src="{MERMAID}"></script>' if diagramas else ""
    return (f'<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>{titulo}</title>'
            f"<style>{ESTILOS}</style>{guion}</head><body>{cuerpo}</body></html>"), diagramas


def preparar(texto):
    """Dentro de un bloque <div> el Markdown no se interpreta, salvo que el bloque lo pida."""
    return texto.replace('<div class="portada">', '<div class="portada" markdown="1">')


def dibujar_diagramas(pagina):
    try:
        pagina.wait_for_function("window.mermaid !== undefined", timeout=TIEMPO_ESPERA_MS)
        pagina.evaluate("mermaid.initialize({ startOnLoad: false, theme: 'neutral' }); mermaid.run()")
        pagina.wait_for_function(
            "[...document.querySelectorAll('pre.mermaid')].every((d) => d.querySelector('svg'))", timeout=TIEMPO_ESPERA_MS)
        return True
    except ErrorPlaywright:
        return False


def main(argumentos=None):
    parser = argparse.ArgumentParser(description="Convierte un documento Markdown en PDF.")
    parser.add_argument("documento", help="Ruta del archivo .md")
    args = parser.parse_args(argumentos)
    load_dotenv()

    origen = Path(args.documento)
    if not origen.is_file():
        print(f"No existe el documento: {origen}", file=sys.stderr)
        return 2
    html, diagramas = a_html(preparar(origen.read_text(encoding="utf-8")), origen.stem)
    # El HTML se guarda junto al Markdown para que las rutas de las imágenes sigan siendo válidas.
    temporal = origen.with_suffix(".tmp.html")
    destino = origen.with_suffix(".pdf")
    temporal.write_text(html, encoding="utf-8")
    try:
        with sync_playwright() as playwright:
            navegador = playwright.chromium.launch(executable_path=os.getenv("CAPTURAS_NAVEGADOR") or None)
            pagina = navegador.new_page()
            pagina.goto(temporal.resolve().as_uri(), wait_until="load")
            if diagramas and not dibujar_diagramas(pagina):
                print("AVISO: no se pudieron dibujar los diagramas (¿sin internet?); quedan como texto.")
            pagina.pdf(path=str(destino), format="Letter", print_background=True, prefer_css_page_size=True)
            navegador.close()
    finally:
        temporal.unlink(missing_ok=True)
    print(f"PDF generado: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
