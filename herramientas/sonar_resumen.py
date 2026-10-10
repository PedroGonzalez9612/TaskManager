"""Resumen del último análisis de SonarQube del proyecto, en la terminal.

Uso (desde la raíz del proyecto, con SONAR_TOKEN en el .env):
    python herramientas/sonar_resumen.py

Muestra la puerta de calidad, las medidas principales y los hallazgos abiertos con su archivo y
línea. El servidor y el proyecto se leen de sonar-project.properties."""
import base64
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
MEDIDAS = ("alert_status,bugs,vulnerabilities,security_hotspots,code_smells,coverage,"
           "duplicated_lines_density,ncloc,reliability_rating,security_rating,sqale_rating")
LETRA = {"1.0": "A", "2.0": "B", "3.0": "C", "4.0": "D", "5.0": "E"}


def leer_propiedades():
    propiedades = {}
    for linea in (RAIZ / "sonar-project.properties").read_text(encoding="utf-8").splitlines():
        if "=" in linea and not linea.lstrip().startswith("#"):
            clave, valor = linea.split("=", 1)
            propiedades[clave.strip()] = valor.strip()
    return propiedades


def pedir(servidor, token, ruta, **parametros):
    peticion = urllib.request.Request(f"{servidor}{ruta}?{urllib.parse.urlencode(parametros)}")
    credencial = base64.b64encode(f"{token}:".encode()).decode()
    peticion.add_header("Authorization", f"Basic {credencial}")
    with urllib.request.urlopen(peticion, timeout=30) as respuesta:
        return json.load(respuesta)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    load_dotenv(RAIZ / ".env")
    token = os.getenv("SONAR_TOKEN")
    if not token:
        sys.exit("Falta SONAR_TOKEN en el .env.")
    propiedades = leer_propiedades()
    servidor, proyecto = propiedades["sonar.host.url"], propiedades["sonar.projectKey"]

    puerta = pedir(servidor, token, "/api/qualitygates/project_status", projectKey=proyecto)["projectStatus"]
    print(f"Puerta de calidad: {'PASA' if puerta['status'] == 'OK' else 'NO PASA'}")
    for condicion in puerta.get("conditions", []):
        estado = "bien" if condicion["status"] == "OK" else "FALLA"
        print(f"  {estado:<5} {condicion['metricKey']}: {condicion.get('actualValue')} (límite {condicion.get('errorThreshold')})")

    medidas = pedir(servidor, token, "/api/measures/component", component=proyecto, metricKeys=MEDIDAS)
    print("\nMedidas:")
    for medida in sorted(medidas["component"]["measures"], key=lambda m: m["metric"]):
        valor = medida.get("value", "")
        if medida["metric"].endswith("_rating"):
            valor = LETRA.get(valor, valor)
        print(f"  {medida['metric']:<28} {valor}")

    hallazgos = pedir(servidor, token, "/api/issues/search", components=proyecto, ps=500,
                      issueStatuses="OPEN,CONFIRMED")
    print(f"\nHallazgos abiertos: {hallazgos['total']}")
    for hallazgo in sorted(hallazgos["issues"], key=lambda h: (h["component"], h.get("line", 0))):
        archivo = hallazgo["component"].split(":", 1)[1]
        print(f"  {hallazgo['severity']:<8} {archivo}:{hallazgo.get('line', '')}  {hallazgo['rule']}  {hallazgo['message'][:120]}")

    puntos = pedir(servidor, token, "/api/hotspots/search", project=proyecto, ps=500, status="TO_REVIEW")
    print(f"\nPuntos de seguridad por revisar: {puntos['paging']['total']}")
    for punto in puntos.get("hotspots", []):
        archivo = punto["component"].split(":", 1)[1]
        print(f"  {punto['vulnerabilityProbability']:<6} {archivo}:{punto.get('line', '')}  {punto['message'][:120]}")


if __name__ == "__main__":
    main()
