"""Pruebas de las rutas de ejecución: reciben la petición, llaman al servicio y responden en JSON.
Se monta solo el blueprint de actividades sobre la base en memoria (create_app se conectaría a MongoDB)."""
import pytest
from flask import Flask, jsonify

from app.routes.actividad_routes import create_blueprint
from app.utils.errors import ErrorApi


@pytest.fixture
def aplicacion(db, reloj):
    app = Flask(__name__)
    app.config.update(SECRET_KEY="pruebas", TESTING=True)
    app.register_blueprint(create_blueprint(db, reloj=reloj))    # Con el reloj de la prueba.

    @app.errorhandler(ErrorApi)    # El mismo manejador de app/__init__.py.
    def manejar_error_api(error):
        return jsonify({"error": str(error)}), error.status_code

    return app


@pytest.fixture
def entrar(aplicacion):
    """Devuelve un cliente con la sesión de ese usuario ya iniciada."""
    def _entrar(usuario):
        cliente = aplicacion.test_client()
        with cliente.session_transaction() as sesion:
            sesion["usuario"] = usuario
        return cliente
    return _entrar


def test_ciclo_completo_por_la_api(entrar, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    ana = entrar(empresa.ana)
    base = f"/actividades/{actividad['id']}"

    iniciada = ana.post(f"{base}/iniciar")
    assert iniciada.status_code == 200
    assert iniciada.get_json()["estado"] == "EN_EJECUCION"
    assert iniciada.get_json()["ejecucion"]["fecha_inicio"]

    sin_motivo = ana.post(f"{base}/pausar")
    assert sin_motivo.status_code == 400
    assert sin_motivo.get_json()["error"]

    pausada = ana.post(f"{base}/pausar", json={"motivo": "Falta material"})
    assert pausada.status_code == 200
    assert pausada.get_json()["estado"] == "PAUSADA"
    assert pausada.get_json()["ejecucion"]["pausas"][0]["motivo"] == "Falta material"

    assert ana.post(f"{base}/reanudar").get_json()["estado"] == "EN_EJECUCION"

    finalizada = ana.post(f"{base}/finalizar", json={"observacion": "Todo en orden"})
    assert finalizada.status_code == 200
    assert finalizada.get_json()["estado"] == "COMPLETADA"
    assert finalizada.get_json()["ejecucion"]["observacion"] == "Todo en orden"
    assert ana.get(base).get_json()["estado"] == "COMPLETADA"


def test_finalizar_funciona_sin_cuerpo(entrar, empresa, crear_actividad):
    """La interfaz actual llama a /finalizar sin cuerpo."""
    actividad = crear_actividad([empresa.ana])
    ana = entrar(empresa.ana)
    ana.post(f"/actividades/{actividad['id']}/iniciar")

    respuesta = ana.post(f"/actividades/{actividad['id']}/finalizar")
    assert respuesta.status_code == 200
    assert respuesta.get_json()["ejecucion"]["observacion"] is None


@pytest.mark.parametrize("accion", ["iniciar", "pausar", "reanudar", "finalizar"])
def test_la_ejecucion_es_solo_del_operario(aplicacion, entrar, empresa, crear_actividad, accion):
    actividad = crear_actividad([empresa.ana])
    ruta = f"/actividades/{actividad['id']}/{accion}"

    assert aplicacion.test_client().post(ruta).status_code == 401
    assert entrar(empresa.admin).post(ruta).status_code == 403
    assert entrar(empresa.luis).post(ruta).status_code == 403    # Operario, pero no la tiene asignada.
