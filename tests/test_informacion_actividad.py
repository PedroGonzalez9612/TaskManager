"""Pruebas de la información de la actividad (alcance, Sección 5.1): los bloques que el Administrador
deja para hacer el trabajo, sus sugerencias, sus adjuntos y "Lista para iniciar"."""
import io

import pytest

from app.models.informacion_actividad import (
    MAXIMO_VALORES_POR_BLOQUE, BloqueInformacion, InformacionActividad,
)
from app.models.adjunto import MAXIMO_POR_ACTIVIDAD
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError

pytestmark = pytest.mark.usefixtures("con_entrada_marcada")

PDF = b"%PDF-1.4\n" + b"pdf" * 20
FOTO = b"\xff\xd8\xff\xe0" + b"jpg" * 20

INFORMACION = {
    "bloques": ["PASOS", "HERRAMIENTAS", "PRECAUCIONES"],
    "pasos": ["Apagar la selladora", "Cambiar las bandas", "Probar con 10 bolsas"],
    "herramientas": ["Llave de 13 mm", "Bandas nuevas"],
    "precauciones": ["Bloquear y etiquetar la máquina"],
}


# ---------- La clase InformacionActividad ----------

def test_sin_bloques_elegidos_esta_lista_para_iniciar():
    assert InformacionActividad().lista_para_iniciar()
    assert InformacionActividad.desde_datos(None).faltantes() == []


def test_un_bloque_elegido_sin_contenido_es_lo_que_falta():
    informacion = InformacionActividad.desde_datos({"bloques": ["PASOS", "CONTACTO"], "pasos": ["Apagar"]})
    assert informacion.faltantes() == [BloqueInformacion.CONTACTO]
    assert not informacion.lista_para_iniciar()


def test_los_adjuntos_se_cuentan_aparte():
    informacion = InformacionActividad.desde_datos({"bloques": ["ADJUNTOS"]})
    assert informacion.faltantes(cantidad_adjuntos=0) == [BloqueInformacion.ADJUNTOS]
    assert informacion.lista_para_iniciar(cantidad_adjuntos=1)


def test_solo_se_guarda_el_contenido_de_los_bloques_elegidos():
    informacion = InformacionActividad.desde_datos({"bloques": ["PASOS"], "pasos": ["Apagar"],
                                                    "herramientas": ["Llave"]})
    assert informacion.to_dict()["herramientas"] == []


def test_los_valores_se_limpian_sin_perder_el_orden_de_los_pasos():
    informacion = InformacionActividad.desde_datos({
        "bloques": ["PASOS"], "pasos": ["  Apagar   la máquina ", "", "Limpiar", "apagar la máquina", "Encender"],
    })
    assert informacion.to_dict()["pasos"] == ["Apagar la máquina", "Limpiar", "Encender"]


def test_los_bloques_quedan_en_su_orden_aunque_lleguen_desordenados():
    informacion = InformacionActividad.desde_datos({"bloques": ["CONTACTO", "PASOS", "PASOS"]})
    assert informacion.bloques == [BloqueInformacion.PASOS, BloqueInformacion.CONTACTO]


@pytest.mark.parametrize("datos, mensaje", [
    ({"bloques": ["RECETA"]}, "no existe"),
    ({"bloques": "PASOS"}, "lista"),
    ({"bloques": ["PASOS"], "pasos": "Apagar"}, "lista"),
    ({"bloques": ["PASOS"], "pasos": ["x" * 201]}, "200"),
    ({"bloques": ["PASOS"], "pasos": [f"Paso {n}" for n in range(MAXIMO_VALORES_POR_BLOQUE + 1)]}, "20"),
    ("pasos", "no es válida"),
])
def test_se_rechaza_la_informacion_mal_formada(datos, mensaje):
    with pytest.raises(ValidationError, match=mensaje):
        InformacionActividad.desde_datos(datos)


def test_se_guarda_y_se_reconstruye_igual():
    informacion = InformacionActividad.desde_datos(INFORMACION)
    assert InformacionActividad.desde_documento(informacion.to_dict()).to_dict() == informacion.to_dict()


def test_una_actividad_anterior_no_tiene_bloques():
    assert InformacionActividad.desde_documento(None).bloques == []


# ---------- Crear y editar (Administrador) ----------

def test_la_actividad_se_crea_con_su_informacion_y_el_operario_la_ve(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana], informacion=INFORMACION)
    vista = servicios.actividades.obtener_actividad(actividad["id"], empresa.ana)
    assert vista["informacion"]["pasos"] == INFORMACION["pasos"]
    assert vista["informacion"]["bloques"] == ["PASOS", "HERRAMIENTAS", "PRECAUCIONES"]
    assert vista["lista_para_iniciar"] is True
    assert vista["bloques_faltantes"] == []


def test_si_falta_un_bloque_la_actividad_lo_dice(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana], informacion={"bloques": ["PASOS", "CONTACTO"], "pasos": ["Apagar"]})
    assert actividad["lista_para_iniciar"] is False
    assert actividad["bloques_faltantes"] == ["CONTACTO"]


def test_falta_informacion_no_impide_iniciar(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana], informacion={"bloques": ["CONTACTO"]})
    assert servicios.ejecucion.iniciar(actividad["id"], empresa.ana)["estado"] == "EN_EJECUCION"


def test_sin_informacion_la_actividad_esta_lista(crear_actividad, empresa):
    actividad = crear_actividad([empresa.ana])
    assert actividad["informacion"]["bloques"] == []
    assert actividad["lista_para_iniciar"] is True


def test_editar_cambia_la_informacion(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana], informacion=INFORMACION)
    editada = servicios.actividades.actualizar_actividad(
        actividad["id"], {"informacion": {"bloques": ["CONTACTO"], "contacto": ["Jorge, jefe de planta"]}},
        empresa.admin,
    )
    assert editada["informacion"]["bloques"] == ["CONTACTO"]
    assert editada["informacion"]["pasos"] == []


def test_editar_otros_campos_no_toca_la_informacion(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana], informacion=INFORMACION)
    editada = servicios.actividades.actualizar_actividad(actividad["id"], {"titulo": "Otro título"}, empresa.admin)
    assert editada["informacion"]["pasos"] == INFORMACION["pasos"]


def test_iniciada_la_informacion_ya_no_se_cambia(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana], informacion=INFORMACION)
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    with pytest.raises(ValidationError, match="ya inició"):
        servicios.actividades.actualizar_actividad(actividad["id"], {"informacion": {"bloques": []}}, empresa.admin)


def test_el_detalle_dice_el_nombre_del_proyecto(servicios, empresa, crear_actividad):
    proyecto = servicios.proyectos.crear_proyecto({"nombre": "Parada de la línea 2"}, empresa.admin)
    actividad = crear_actividad([empresa.ana], proyecto_id=proyecto["id"])
    assert actividad["proyecto_nombre"] == "Parada de la línea 2"
    assert crear_actividad([empresa.ana], titulo="Suelta")["proyecto_nombre"] is None


# ---------- Sugerencias (catálogos de la empresa) ----------

def test_lo_escrito_queda_como_sugerencia_para_la_proxima(servicios, empresa, crear_actividad):
    crear_actividad([empresa.ana], informacion=INFORMACION)
    crear_actividad([empresa.ana], informacion={"bloques": ["HERRAMIENTAS"], "herramientas": ["llave de 13 mm", "Grasa"]})
    assert servicios.catalogos.sugerencias(empresa.admin, "HERRAMIENTA") == ["Bandas nuevas", "Grasa", "Llave de 13 mm"]
    assert servicios.catalogos.sugerencias(empresa.admin, "PRECAUCION") == ["Bloquear y etiquetar la máquina"]


def test_los_pasos_no_se_sugieren_y_las_empresas_no_se_mezclan(servicios, empresa, otra_empresa, crear_actividad):
    crear_actividad([empresa.ana], informacion=INFORMACION)
    assert servicios.catalogos.sugerencias(otra_empresa.admin, "HERRAMIENTA") == []
    with pytest.raises(NotFoundError):
        servicios.catalogos.sugerencias(empresa.admin, "PASOS")


def test_las_sugerencias_por_la_api_son_solo_del_administrador(cliente_de, empresa, crear_actividad):
    crear_actividad([empresa.ana], informacion=INFORMACION)
    respuesta = cliente_de(empresa.admin).get("/catalogos/informacion/herramientas")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == ["Bandas nuevas", "Llave de 13 mm"]
    assert cliente_de(empresa.ana).get("/catalogos/informacion/herramientas").status_code == 403
    assert cliente_de(empresa.admin).get("/catalogos/informacion/recetas").status_code == 404


# ---------- Adjuntos ----------

def test_el_administrador_adjunta_y_el_operario_lo_ve(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana], informacion={"bloques": ["ADJUNTOS"]})
    assert actividad["bloques_faltantes"] == ["ADJUNTOS"]

    adjunto = servicios.adjuntos.agregar(actividad["id"], empresa.admin, PDF, "manual de la selladora.pdf")
    vista = servicios.actividades.obtener_actividad(actividad["id"], empresa.ana)
    assert [(a["tipo"], a["nombre"]) for a in vista["informacion"]["adjuntos"]] == [("ADJUNTO", "manual de la selladora.pdf")]
    assert vista["lista_para_iniciar"] is True

    contenido, tipo, nombre = servicios.adjuntos.obtener(actividad["id"], adjunto["id"], empresa.ana)
    assert (contenido, tipo, nombre) == (PDF, "application/pdf", "manual de la selladora.pdf")


def test_solo_el_administrador_adjunta(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    with pytest.raises(ProhibidoError):
        servicios.adjuntos.agregar(actividad["id"], empresa.ana, PDF, "x.pdf")


def test_no_se_adjunta_a_una_actividad_iniciada_ni_de_otra_empresa(servicios, empresa, otra_empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    with pytest.raises(NotFoundError):
        servicios.adjuntos.agregar(actividad["id"], otra_empresa.admin, PDF, "x.pdf")
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    with pytest.raises(ValidationError, match="ya se inició"):
        servicios.adjuntos.agregar(actividad["id"], empresa.admin, PDF, "x.pdf")


def test_maximo_de_adjuntos_por_actividad(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    for numero in range(MAXIMO_POR_ACTIVIDAD):
        servicios.adjuntos.agregar(actividad["id"], empresa.admin, FOTO, f"foto {numero}.jpg")
    with pytest.raises(ValidationError, match="como máximo"):
        servicios.adjuntos.agregar(actividad["id"], empresa.admin, FOTO, "una más.jpg")


def test_quien_no_tiene_la_actividad_no_ve_el_adjunto(servicios, empresa, otra_empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    adjunto = servicios.adjuntos.agregar(actividad["id"], empresa.admin, PDF, "plano.pdf")
    for intruso in (empresa.luis, otra_empresa.admin, otra_empresa.ivan):
        with pytest.raises(NotFoundError):
            servicios.adjuntos.obtener(actividad["id"], adjunto["id"], intruso)
    with pytest.raises(NotFoundError):
        servicios.adjuntos.obtener("otra-actividad", adjunto["id"], empresa.admin)


def test_adjuntar_y_abrir_por_la_api(cliente_de, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    admin = cliente_de(empresa.admin)
    respuesta = admin.post(f"/actividades/{actividad['id']}/adjuntos",
                           data={"archivo": (io.BytesIO(PDF), "plano.pdf")},
                           headers={"X-Requested-With": "GestLab"}, content_type="multipart/form-data")
    assert respuesta.status_code == 201
    adjunto_id = respuesta.get_json()["id"]

    archivo = cliente_de(empresa.ana).get(f"/actividades/{actividad['id']}/adjuntos/{adjunto_id}")
    assert archivo.status_code == 200
    assert archivo.data == PDF
    assert archivo.headers["X-Content-Type-Options"] == "nosniff"
    assert cliente_de(empresa.luis).get(f"/actividades/{actividad['id']}/adjuntos/{adjunto_id}").status_code == 404
