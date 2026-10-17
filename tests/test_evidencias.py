"""Pruebas de la evidencia de la ejecución (alcance, Sección 5.1): fotos y adjuntos que el operario
deja al finalizar, y quién los puede ver."""
import io

import pytest

from app.models.evidencia import MAXIMO_POR_EJECUCION, TAMANO_MAXIMO, Evidencia, TipoEvidencia, limpiar_nombre
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError

# Las pruebas de este módulo ejecutan actividades: los operarios ya marcaron su entrada.
pytestmark = pytest.mark.usefixtures("con_entrada_marcada")

FOTO = b"\xff\xd8\xff\xe0" + b"jpg" * 20
PNG = b"\x89PNG\r\n\x1a\n" + b"png" * 20
PDF = b"%PDF-1.4\n" + b"pdf" * 20


@pytest.fixture
def en_curso(servicios, empresa, crear_actividad):
    """Una actividad que Ana ya tiene en curso."""
    actividad = crear_actividad([empresa.ana])
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    return actividad


def ejecucion_de(servicios, actividad_id, operario):
    return servicios.actividades.obtener_actividad(actividad_id, operario)["ejecucion"]


# ---------- La clase Evidencia ----------

class _Ejecucion:
    id, actividad_id, usuario_id = "e1", "a1", "u1"


@pytest.mark.parametrize("contenido, tipo", [(FOTO, TipoEvidencia.FOTO), (PNG, TipoEvidencia.FOTO),
                                             (PDF, TipoEvidencia.ADJUNTO)])
def test_el_tipo_sale_del_contenido_no_del_nombre(contenido, tipo):
    evidencia = Evidencia.desde_archivo(contenido, "foto.pdf", _Ejecucion(), "emp1", None)
    assert evidencia.tipo == tipo


@pytest.mark.parametrize("contenido", [b"", b"<svg onload='x'>", b"MZ ejecutable", b"texto plano"])
def test_se_rechaza_lo_que_no_es_foto_ni_pdf(contenido):
    ejecucion = _Ejecucion()
    with pytest.raises(ValidationError):
        Evidencia.desde_archivo(contenido, "archivo", ejecucion, "emp1", None)


def test_se_rechaza_un_archivo_de_mas_de_5_mb():
    grande, ejecucion = FOTO + b"0" * TAMANO_MAXIMO, _Ejecucion()
    with pytest.raises(ValidationError, match="5 MB"):
        Evidencia.desde_archivo(grande, "grande.jpg", ejecucion, "emp1", None)


def test_el_nombre_queda_sin_carpeta_y_con_largo_maximo():
    assert limpiar_nombre("C:\\Users\\ana\\fotos\\valvula.jpg") == "valvula.jpg"
    assert limpiar_nombre("../../etc/passwd") == "passwd"
    assert limpiar_nombre("") == "archivo"
    assert len(limpiar_nombre("a" * 300)) == 120


def test_la_evidencia_se_guarda_y_se_reconstruye_igual():
    evidencia = Evidencia.desde_archivo(PDF, "informe.pdf", _Ejecucion(), "emp1", None)
    reconstruida = Evidencia.desde_documento({**evidencia.to_dict(), "_id": "x1"})
    assert reconstruida.presentar() == {**evidencia.presentar(), "id": "x1"}


# ---------- Subir (Operario) ----------

def test_el_operario_deja_fotos_y_adjuntos_y_aparecen_en_su_registro(servicios, empresa, en_curso):
    servicios.evidencias.agregar(en_curso["id"], empresa.ana, FOTO, "valvula.jpg")
    servicios.evidencias.agregar(en_curso["id"], empresa.ana, PDF, "informe.pdf")
    servicios.ejecucion.finalizar(en_curso["id"], empresa.ana, "Cambié el empaque")

    ejecucion = ejecucion_de(servicios, en_curso["id"], empresa.ana)
    assert [(e["tipo"], e["nombre"]) for e in ejecucion["evidencias"]] == [("FOTO", "valvula.jpg"),
                                                                           ("ADJUNTO", "informe.pdf")]
    assert ejecucion["observacion"] == "Cambié el empaque"
    assert "contenido" not in ejecucion["evidencias"][0]


def test_tambien_se_deja_con_la_actividad_pausada(servicios, empresa, en_curso):
    servicios.ejecucion.pausar(en_curso["id"], empresa.ana, "Actividad urgente")
    assert servicios.evidencias.agregar(en_curso["id"], empresa.ana, FOTO, "f.jpg")["tipo"] == "FOTO"


def test_no_se_deja_antes_de_iniciar_ni_despues_de_finalizar(servicios, empresa, crear_actividad, en_curso):
    sin_iniciar = crear_actividad([empresa.ana], titulo="Otra")
    with pytest.raises(ValidationError, match="en curso o pausada"):
        servicios.evidencias.agregar(sin_iniciar["id"], empresa.ana, FOTO, "f.jpg")

    servicios.ejecucion.finalizar(en_curso["id"], empresa.ana)
    with pytest.raises(ValidationError, match="en curso o pausada"):
        servicios.evidencias.agregar(en_curso["id"], empresa.ana, FOTO, "f.jpg")


def test_hay_un_maximo_de_archivos_por_ejecucion(servicios, empresa, en_curso):
    for numero in range(MAXIMO_POR_EJECUCION):
        servicios.evidencias.agregar(en_curso["id"], empresa.ana, FOTO, f"f{numero}.jpg")
    with pytest.raises(ValidationError, match="como máximo"):
        servicios.evidencias.agregar(en_curso["id"], empresa.ana, FOTO, "una_mas.jpg")


def test_solo_el_operario_asignado_deja_evidencia(servicios, empresa, otra_empresa, en_curso):
    with pytest.raises(ProhibidoError):
        servicios.evidencias.agregar(en_curso["id"], empresa.luis, FOTO, "f.jpg")
    with pytest.raises(NotFoundError):
        servicios.evidencias.agregar(en_curso["id"], otra_empresa.ivan, FOTO, "f.jpg")
    with pytest.raises(ProhibidoError):
        servicios.evidencias.agregar(en_curso["id"], empresa.admin, FOTO, "f.jpg")


def test_cada_operario_deja_la_suya(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    for operario in (empresa.ana, empresa.luis):
        servicios.ejecucion.iniciar(actividad["id"], operario)
    servicios.evidencias.agregar(actividad["id"], empresa.ana, FOTO, "de_ana.jpg")

    assert len(ejecucion_de(servicios, actividad["id"], empresa.ana)["evidencias"]) == 1
    assert ejecucion_de(servicios, actividad["id"], empresa.luis)["evidencias"] == []


# ---------- Ver (Operario y Administrador) ----------

def test_la_ven_el_operario_dueno_y_el_administrador_de_su_empresa(servicios, empresa, otra_empresa, en_curso):
    evidencia = servicios.evidencias.agregar(en_curso["id"], empresa.ana, PDF, "informe.pdf")

    for quien in (empresa.ana, empresa.admin):
        contenido, tipo, nombre = servicios.evidencias.obtener(en_curso["id"], evidencia["id"], quien)
        assert (contenido, tipo, nombre) == (PDF, "application/pdf", "informe.pdf")
    for quien in (empresa.luis, otra_empresa.admin):
        with pytest.raises(NotFoundError):
            servicios.evidencias.obtener(en_curso["id"], evidencia["id"], quien)


def test_no_se_ve_por_otra_actividad_ni_con_un_id_inventado(servicios, empresa, crear_actividad, en_curso):
    evidencia = servicios.evidencias.agregar(en_curso["id"], empresa.ana, FOTO, "f.jpg")
    otra = crear_actividad([empresa.ana], titulo="Otra")
    with pytest.raises(NotFoundError):
        servicios.evidencias.obtener(otra["id"], evidencia["id"], empresa.admin)
    with pytest.raises(NotFoundError):
        servicios.evidencias.obtener(en_curso["id"], "no-es-un-id", empresa.admin)


def test_el_administrador_ve_la_evidencia_en_el_detalle(servicios, empresa, en_curso):
    servicios.evidencias.agregar(en_curso["id"], empresa.ana, FOTO, "valvula.jpg")
    detalle = servicios.actividades.obtener_actividad(en_curso["id"], empresa.admin)
    assert [e["nombre"] for e in detalle["ejecuciones"][0]["evidencias"]] == ["valvula.jpg"]


# ---------- Por la API ----------

def test_subir_y_abrir_por_la_api(cliente_de, empresa, en_curso):
    ana, admin = cliente_de(empresa.ana), cliente_de(empresa.admin)
    ruta = f"/actividades/{en_curso['id']}/evidencias"

    subida = ana.post(ruta, data={"archivo": (io.BytesIO(FOTO), "valvula.jpg")},
                      headers={"X-Requested-With": "GestLab"}, content_type="multipart/form-data")
    assert subida.status_code == 201
    evidencia_id = subida.get_json()["id"]

    abierta = admin.get(f"{ruta}/{evidencia_id}")
    assert abierta.status_code == 200
    assert abierta.data == FOTO
    assert abierta.mimetype == "image/jpeg"
    assert abierta.headers["X-Content-Type-Options"] == "nosniff"
    assert abierta.headers["Content-Disposition"].startswith("inline;")

    sin_archivo = ana.post(ruta, data={}, headers={"X-Requested-With": "GestLab"}, content_type="multipart/form-data")
    assert sin_archivo.status_code == 400
    assert admin.post(ruta, data={"archivo": (io.BytesIO(FOTO), "f.jpg")}, headers={"X-Requested-With": "GestLab"},
                      content_type="multipart/form-data").status_code == 403
