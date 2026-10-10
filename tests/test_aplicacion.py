"""Pruebas de la aplicación completa, armada con create_app sobre una base en memoria: arranque,
protección contra CSRF, inicio de sesión, empresas, usuarios, requerimientos y carga laboral."""
import io

import mongomock
import pytest

import app.extensions
from app import create_app
from app.config import Config

PROPIA = {"X-Requested-With": "GestLab"}    # El encabezado que pone la interfaz (app/static/js/api.js).
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32
CLAVE = "Clave12345"
# Aquí la hora es la real del servidor: una fecha lejana para que el cierre de jornada no reprograme
# las actividades de estas pruebas cuando pase el día.
FECHA = "2099-10-10"


class ConfiguracionDePrueba(Config):
    TESTING = True
    SECRET_KEY = "pruebas"
    SUPERADMIN_NOMBRE = "Superadmin"
    SUPERADMIN_CORREO = "super@prueba.co"
    SUPERADMIN_CONTRASENA = CLAVE


@pytest.fixture
def aplicacion(monkeypatch):
    monkeypatch.setattr(app.extensions, "MongoClient", mongomock.MongoClient)
    return create_app(ConfiguracionDePrueba)


class Cliente:
    """Cliente HTTP que se comporta como la interfaz: siempre manda el encabezado propio."""

    def __init__(self, aplicacion, correo=None):
        self.http = aplicacion.test_client()
        if correo:
            respuesta = self.post("/auth/login", {"correo": correo, "contraseña": CLAVE})
            assert respuesta.status_code == 200, respuesta.get_json()

    def get(self, ruta):
        return self.http.get(ruta)

    def post(self, ruta, datos=None):
        return self.http.post(ruta, json=datos or {}, headers=PROPIA)

    def put(self, ruta, datos=None):
        return self.http.put(ruta, json=datos or {}, headers=PROPIA)

    def delete(self, ruta):
        return self.http.delete(ruta, headers=PROPIA)

    def subir_logo(self, empresa_id, contenido):
        return self.http.put(f"/empresas/{empresa_id}/logo", headers=PROPIA,
                             data={"logo": (io.BytesIO(contenido), "logo.png")}, content_type="multipart/form-data")


@pytest.fixture
def superadmin(aplicacion):
    return Cliente(aplicacion, "super@prueba.co")


def datos_empresa(**cambios):
    return {"nombre": "Metálicas SAS", "nit": "900123", "sector": "Manufactura", "direccion": "Calle 1",
            "limite_administradores": 2, "limite_operarios": 2, **cambios}


@pytest.fixture
def empresa(superadmin):
    respuesta = superadmin.post("/empresas", datos_empresa())
    assert respuesta.status_code == 201
    return respuesta.get_json()


def crear_usuario(cliente, nombre, rol, **extra):
    return cliente.post("/usuarios", {"nombre": nombre, "correo": f"{nombre.lower()}@prueba.co",
                                      "contraseña": CLAVE, "rol": rol, **extra})


@pytest.fixture
def admin(aplicacion, superadmin, empresa):
    assert crear_usuario(superadmin, "Ana", "ADMINISTRADOR", empresa_id=empresa["id"]).status_code == 201
    return Cliente(aplicacion, "ana@prueba.co")


# ---------- Arranque ----------

def test_la_aplicacion_arranca_y_responde(aplicacion):
    cliente = Cliente(aplicacion)
    assert cliente.get("/health").get_json() == {"status": "ok"}
    assert cliente.get("/").headers["Location"].endswith("/static/login.html")


def test_el_superadmin_inicial_se_crea_una_sola_vez(monkeypatch):
    unico = mongomock.MongoClient()
    monkeypatch.setattr(app.extensions, "MongoClient", lambda uri: unico)
    create_app(ConfiguracionDePrueba)
    create_app(ConfiguracionDePrueba)
    assert unico[Config.MONGO_DB_NAME]["usuarios"].count_documents({"rol": "SUPERADMIN"}) == 1


def test_la_base_no_se_puede_usar_antes_de_iniciarla(monkeypatch):
    monkeypatch.setattr(app.extensions, "_db", None)
    with pytest.raises(RuntimeError):
        app.extensions.get_db()


# ---------- Protección contra CSRF ----------

def test_una_peticion_que_cambia_datos_sin_el_encabezado_se_rechaza(aplicacion):
    respuesta = aplicacion.test_client().post("/auth/login", json={"correo": "super@prueba.co", "contraseña": CLAVE})
    assert respuesta.status_code == 403


def test_con_sesion_abierta_otra_pagina_no_puede_cambiar_datos(aplicacion, superadmin):
    # La cookie de sesión viaja, pero la petición no trae el encabezado de la interfaz.
    respuesta = superadmin.http.post("/empresas", json=datos_empresa())
    assert respuesta.status_code == 403
    assert superadmin.get("/empresas").get_json() == []


def test_las_consultas_no_necesitan_el_encabezado(aplicacion):
    assert aplicacion.test_client().get("/health").status_code == 200


def test_la_cookie_de_sesion_no_viaja_a_otros_sitios(aplicacion):
    respuesta = aplicacion.test_client().post(
        "/auth/login", json={"correo": "super@prueba.co", "contraseña": CLAVE}, headers=PROPIA)
    cookie = respuesta.headers["Set-Cookie"]
    assert "SameSite=Lax" in cookie
    assert "HttpOnly" in cookie


# ---------- Inicio de sesión ----------

@pytest.mark.parametrize("datos", [
    {"correo": "super@prueba.co", "contraseña": "equivocada"},
    {"correo": "nadie@prueba.co", "contraseña": CLAVE},
    {"correo": "", "contraseña": ""},
])
def test_credenciales_malas_dan_el_mismo_error(aplicacion, datos):
    respuesta = Cliente(aplicacion).post("/auth/login", datos)
    assert respuesta.status_code == 401
    assert respuesta.get_json() == {"error": "Correo o contraseña incorrectos"}


def test_sesion_del_superadmin_y_cierre(superadmin):
    sesion = superadmin.get("/auth/sesion").get_json()
    assert sesion["rol"] == "SUPERADMIN"
    assert sesion["empresa"] is None
    assert "contraseña_hash" not in sesion

    assert superadmin.post("/auth/logout").status_code == 204
    assert superadmin.get("/auth/sesion").status_code == 401


def test_la_sesion_de_una_empresa_trae_su_marca(admin, superadmin, empresa):
    assert admin.get("/auth/sesion").get_json()["empresa"] == {"nombre": "Metálicas SAS", "tiene_logo": False}
    assert superadmin.subir_logo(empresa["id"], PNG).status_code == 200
    assert admin.get("/auth/sesion").get_json()["empresa"]["tiene_logo"] is True


# ---------- Empresas ----------

@pytest.mark.parametrize("cambios", [
    {"nombre": "  "},
    {"limite_operarios": "muchos"},
    {"limite_administradores": 0},
])
def test_crear_empresa_valida_sus_datos(superadmin, cambios):
    assert superadmin.post("/empresas", datos_empresa(**cambios)).status_code == 400


def test_el_nit_no_se_repite(superadmin, empresa):
    assert superadmin.post("/empresas", datos_empresa(nombre="Otra")).status_code == 400


def test_solo_el_superadmin_administra_empresas(admin, empresa):
    assert admin.get("/empresas").status_code == 403
    assert admin.post("/empresas", datos_empresa(nit="1")).status_code == 403
    assert admin.get(f"/empresas/{empresa['id']}").status_code == 200


def test_listar_y_editar_una_empresa(superadmin, empresa):
    assert [e["nombre"] for e in superadmin.get("/empresas").get_json()] == ["Metálicas SAS"]

    editada = superadmin.put(f"/empresas/{empresa['id']}", {"nombre": "Metálicas del Valle", "limite_operarios": 5})
    assert editada.status_code == 200
    assert editada.get_json()["nombre"] == "Metálicas del Valle"
    assert editada.get_json()["limite_operarios"] == 5


@pytest.mark.parametrize("datos", [{}, {"nombre": ""}, {"limite_operarios": "x"}])
def test_editar_empresa_rechaza_datos_invalidos(superadmin, empresa, datos):
    assert superadmin.put(f"/empresas/{empresa['id']}", datos).status_code == 400


def test_un_limite_no_baja_de_los_usuarios_que_ya_hay(superadmin, admin, empresa):
    assert crear_usuario(superadmin, "Beto", "ADMINISTRADOR", empresa_id=empresa["id"]).status_code == 201
    respuesta = superadmin.put(f"/empresas/{empresa['id']}", {"limite_administradores": 1})
    assert respuesta.status_code == 400
    assert "ya tiene 2 administradores" in respuesta.get_json()["error"]


def test_una_empresa_que_no_existe_da_404(superadmin):
    assert superadmin.get("/empresas/000000000000000000000000").status_code == 404
    assert superadmin.delete("/empresas/no-es-un-id").status_code == 404


def test_eliminar_una_empresa(superadmin, empresa):
    assert superadmin.delete(f"/empresas/{empresa['id']}").status_code == 204
    assert superadmin.get(f"/empresas/{empresa['id']}").status_code == 404


# ---------- Zona horaria ----------

def test_una_empresa_nace_con_la_zona_horaria_por_defecto(empresa):
    assert empresa["zona_horaria"] == "America/Bogota"


def test_crear_una_empresa_con_su_zona_horaria(superadmin):
    respuesta = superadmin.post("/empresas", datos_empresa(zona_horaria="Asia/Tokyo"))
    assert respuesta.status_code == 201
    assert respuesta.get_json()["zona_horaria"] == "Asia/Tokyo"
    assert superadmin.get("/empresas").get_json()[0]["zona_horaria"] == "Asia/Tokyo"


@pytest.mark.parametrize("zona", ["Marte/Olimpo", "bogota", 5])
def test_crear_una_empresa_con_una_zona_que_no_existe_da_400(superadmin, zona):
    respuesta = superadmin.post("/empresas", datos_empresa(zona_horaria=zona))
    assert respuesta.status_code == 400
    assert "zona horaria" in respuesta.get_json()["error"]
    assert superadmin.get("/empresas").get_json() == []


def test_el_superadmin_cambia_la_zona_horaria(superadmin, empresa):
    editada = superadmin.put(f"/empresas/{empresa['id']}", {"zona_horaria": "Europe/Madrid"})
    assert editada.status_code == 200
    assert editada.get_json()["zona_horaria"] == "Europe/Madrid"
    assert editada.get_json()["nombre"] == "Metálicas SAS"


@pytest.mark.parametrize("zona", ["Marte/Olimpo", "", None])
def test_cambiar_a_una_zona_que_no_existe_da_400_y_no_cambia_nada(superadmin, empresa, zona):
    assert superadmin.put(f"/empresas/{empresa['id']}", {"zona_horaria": zona}).status_code == 400
    assert superadmin.get(f"/empresas/{empresa['id']}").get_json()["zona_horaria"] == "America/Bogota"


def test_el_administrador_ve_la_zona_pero_no_la_cambia(admin, empresa):
    assert admin.put(f"/empresas/{empresa['id']}", {"zona_horaria": "Asia/Tokyo"}).status_code == 403
    assert admin.get(f"/empresas/{empresa['id']}").get_json()["zona_horaria"] == "America/Bogota"


# ---------- Logo ----------

@pytest.mark.parametrize("contenido, motivo", [
    pytest.param(b"", "Selecciona una imagen", id="vacio"),
    pytest.param(b"<svg></svg>", "PNG, JPG o WEBP", id="svg"),
    pytest.param(PNG + b"0" * (513 * 1024), "512 KB", id="muy-pesado"),
])
def test_el_logo_se_valida_por_su_contenido(superadmin, empresa, contenido, motivo):
    respuesta = superadmin.subir_logo(empresa["id"], contenido)
    assert respuesta.status_code == 400
    assert motivo in respuesta.get_json()["error"]


@pytest.mark.parametrize("contenido, tipo", [
    pytest.param(PNG, "image/png", id="png"),
    pytest.param(b"\xff\xd8\xff" + b"0" * 16, "image/jpeg", id="jpg"),
    pytest.param(b"RIFF0000WEBP" + b"0" * 16, "image/webp", id="webp"),
])
def test_el_logo_se_guarda_y_se_sirve_con_su_tipo(superadmin, empresa, contenido, tipo):
    assert superadmin.subir_logo(empresa["id"], contenido).get_json()["tiene_logo"] is True
    logo = superadmin.get(f"/empresas/{empresa['id']}/logo")
    assert logo.mimetype == tipo
    assert logo.data == contenido
    assert logo.headers["X-Content-Type-Options"] == "nosniff"


def test_sin_logo_no_hay_nada_que_servir(superadmin, empresa):
    assert superadmin.get(f"/empresas/{empresa['id']}/logo").status_code == 404


def test_un_archivo_enorme_se_rechaza_antes_de_leerlo(superadmin, empresa):
    respuesta = superadmin.subir_logo(empresa["id"], b"0" * (2 * 1024 * 1024))
    assert respuesta.status_code == 413
    assert respuesta.get_json() == {"error": "El archivo es demasiado grande"}


# ---------- Usuarios ----------

def test_el_superadmin_solo_crea_administradores(superadmin, empresa):
    assert crear_usuario(superadmin, "Leo", "OPERARIO", empresa_id=empresa["id"]).status_code == 403
    assert crear_usuario(superadmin, "Leo", "ADMINISTRADOR").status_code == 400    # Falta la empresa.
    assert crear_usuario(superadmin, "Leo", "ADMINISTRADOR",
                         empresa_id="000000000000000000000000").status_code == 404


@pytest.mark.parametrize("cambios", [{"nombre": ""}, {"contraseña": "corta"}, {"rol": "SUPERADMIN"}])
def test_crear_usuario_valida_sus_datos(admin, cambios):
    datos = {"nombre": "Leo", "correo": "leo@prueba.co", "contraseña": CLAVE, "rol": "OPERARIO", **cambios}
    assert admin.post("/usuarios", datos).status_code == 400


def test_el_administrador_crea_usuarios_solo_en_su_empresa(aplicacion, superadmin, admin, empresa):
    otra = superadmin.post("/empresas", datos_empresa(nombre="Otra", nit="901")).get_json()
    creado = crear_usuario(admin, "Carlos", "OPERARIO", empresa_id=otra["id"])    # Intenta en otra empresa.
    assert creado.status_code == 201
    assert creado.get_json()["empresa_id"] == empresa["id"]
    assert "contraseña_hash" not in creado.get_json()

    assert crear_usuario(admin, "Carlos", "OPERARIO").status_code == 400            # Correo repetido.
    assert Cliente(aplicacion, "carlos@prueba.co").get("/auth/sesion").get_json()["rol"] == "OPERARIO"


def test_no_se_supera_el_limite_de_usuarios(admin):
    assert crear_usuario(admin, "Carlos", "OPERARIO").status_code == 201
    assert crear_usuario(admin, "Luisa", "OPERARIO").status_code == 201
    respuesta = crear_usuario(admin, "Pedro", "OPERARIO")
    assert respuesta.status_code == 400
    assert "límite de 2 operarios" in respuesta.get_json()["error"]


def test_listar_consultar_editar_y_eliminar_usuarios(aplicacion, superadmin, admin, empresa):
    carlos = crear_usuario(admin, "Carlos", "OPERARIO").get_json()

    assert sorted(u["nombre"] for u in admin.get("/usuarios").get_json()) == ["Ana", "Carlos"]
    assert superadmin.get("/usuarios").status_code == 400                          # Falta la empresa.
    assert len(superadmin.get(f"/usuarios?empresa_id={empresa['id']}").get_json()) == 2

    assert admin.get(f"/usuarios/{carlos['id']}").get_json()["correo"] == "carlos@prueba.co"
    assert admin.put(f"/usuarios/{carlos['id']}", {"nombre": "Carlos Ramírez"}).get_json()["nombre"] == "Carlos Ramírez"
    assert admin.put(f"/usuarios/{carlos['id']}", {"nombre": ""}).status_code == 400
    assert admin.get("/usuarios/000000000000000000000000").status_code == 404

    yo = admin.get("/auth/sesion").get_json()["id"]
    assert admin.delete(f"/usuarios/{yo}").status_code == 400                      # No se elimina a sí mismo.
    assert Cliente(aplicacion, "carlos@prueba.co").get("/usuarios").status_code == 403
    assert admin.delete(f"/usuarios/{carlos['id']}").status_code == 204
    assert admin.get(f"/usuarios/{carlos['id']}").status_code == 404


def test_un_administrador_no_ve_los_usuarios_ni_el_logo_de_otra_empresa(aplicacion, superadmin, admin):
    otra = superadmin.post("/empresas", datos_empresa(nombre="Otra", nit="901")).get_json()
    rosa = crear_usuario(superadmin, "Rosa", "ADMINISTRADOR", empresa_id=otra["id"]).get_json()
    superadmin.subir_logo(otra["id"], PNG)

    assert admin.get(f"/usuarios/{rosa['id']}").status_code == 403
    assert admin.get(f"/empresas/{otra['id']}").status_code == 403
    assert admin.get(f"/empresas/{otra['id']}/logo").status_code == 403


# ---------- Requerimientos ----------

def test_ciclo_de_un_requerimiento(admin):
    assert admin.post("/requerimientos", {"titulo": " "}).status_code == 400
    creado = admin.post("/requerimientos", {"titulo": "Mantenimiento de octubre", "descripcion": "Línea 2"})
    assert creado.status_code == 201
    requerimiento = creado.get_json()
    assert requerimiento["actividades"] == 0

    ruta = f"/requerimientos/{requerimiento['id']}"
    assert admin.get(ruta).get_json()["titulo"] == "Mantenimiento de octubre"
    assert admin.put(ruta, {"titulo": "Mantenimiento", "descripcion": "", "estado": "EN_PROCESO"}).get_json()["estado"] == "EN_PROCESO"
    for invalido in ({}, {"titulo": ""}, {"estado": "INVENTADO"}):
        assert admin.put(ruta, invalido).status_code == 400
    assert [r["titulo"] for r in admin.get("/requerimientos").get_json()] == ["Mantenimiento"]


def test_un_requerimiento_de_otra_empresa_no_existe_para_mi(aplicacion, superadmin, admin):
    otra = superadmin.post("/empresas", datos_empresa(nombre="Otra", nit="901")).get_json()
    crear_usuario(superadmin, "Rosa", "ADMINISTRADOR", empresa_id=otra["id"])
    ajeno = Cliente(aplicacion, "rosa@prueba.co").post("/requerimientos", {"titulo": "Ajeno"}).get_json()
    assert admin.get(f"/requerimientos/{ajeno['id']}").status_code == 404


def test_eliminar_un_requerimiento_se_lleva_sus_actividades(admin):
    carlos = crear_usuario(admin, "Carlos", "OPERARIO").get_json()
    requerimiento = admin.post("/requerimientos", {"titulo": "General"}).get_json()
    actividad = admin.post("/actividades", {
        "titulo": "Calibrar", "ubicacion": "Línea 1", "categoria": "MANTENIMIENTO", "tiempo_estimado_min": 60,
        "fecha_programada": FECHA, "requerimiento_id": requerimiento["id"], "operario_ids": [carlos["id"]],
    })
    assert actividad.status_code == 201
    assert admin.get(f"/requerimientos/{requerimiento['id']}").get_json()["actividades"] == 1

    assert admin.delete(f"/requerimientos/{requerimiento['id']}").status_code == 204
    assert admin.get(f"/actividades/{actividad.get_json()['id']}").status_code == 404
    assert admin.get("/requerimientos").get_json() == []


# ---------- Carga laboral ----------

def test_la_carga_suma_lo_programado_y_avisa_la_sobrecarga(aplicacion, admin):
    carlos = crear_usuario(admin, "Carlos", "OPERARIO").get_json()
    for minutos in (300, 240):
        admin.post("/actividades", {
            "titulo": "Producción", "ubicacion": "Línea 1", "categoria": "PRODUCCION",
            "tiempo_estimado_min": minutos, "fecha_programada": FECHA, "operario_ids": [carlos["id"]],
        })

    carga = admin.get(f"/analisis/carga?desde={FECHA}&hasta={FECHA}").get_json()
    jornada = carga["operarios"][0]["jornadas"][0]
    assert carga["capacidad_min"] == 420
    assert jornada["minutos"] == 540
    assert jornada["sobrecarga"] is True

    propia = Cliente(aplicacion, "carlos@prueba.co").get(f"/analisis/carga?desde={FECHA}&hasta={FECHA}")
    assert [o["nombre"] for o in propia.get_json()["operarios"]] == ["Carlos"]
    assert admin.get("/analisis/carga?desde=ayer&hasta=hoy").status_code == 400


# ---------- Turnos y asistencia ----------

def test_turno_y_asistencia_de_extremo_a_extremo(aplicacion, admin):
    carlos = crear_usuario(admin, "Carlos", "OPERARIO").get_json()
    turno = admin.post("/turnos", {"nombre": "Mañana", "hora_inicio": "06:00", "hora_fin": "14:00",
                                   "descanso_min": 60}).get_json()
    assert admin.put(f"/usuarios/{carlos['id']}/turno", {"turno_id": turno["id"]}).status_code == 200
    assert {u["nombre"]: u.get("turno") for u in admin.get("/usuarios").get_json()}["Carlos"]["nombre"] == "Mañana"

    operario = Cliente(aplicacion, "carlos@prueba.co")
    # Sin el encabezado de la interfaz, la marca se rechaza (CSRF).
    assert operario.http.post("/asistencia/entrada").status_code == 403
    assert operario.post("/asistencia/entrada").status_code == 201
    assert operario.get("/asistencia/hoy").get_json()["estado"] == "REGISTRADA"
    assert [f["operario"] for f in admin.get("/asistencias").get_json()] == ["Carlos"]
