"""Piezas compartidas por las pruebas de servicios y rutas.

La base de datos es mongomock (en memoria): ninguna prueba se conecta a un MongoDB real. Se crean
los mismos índices que en producción, porque de ellos depende la regla "una sola actividad en
curso por operario" cuando llegan dos peticiones a la vez."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import mongomock
import pytest

from app.repositories import crear_indices
from app.repositories.actividad_repository import ActividadRepository
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.catalogo_repository import CatalogoRepository
from app.repositories.ejecucion_repository import EjecucionRepository
from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.proyecto_repository import ProyectoRepository
from app.repositories.requerimiento_repository import RequerimientoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.composicion import construir_servicios

HOY = "2026-10-10"


class Reloj:
    """Reloj que la prueba controla: los servicios lo llaman en lugar de leer la hora real."""

    def __init__(self, inicio):
        self.ahora = inicio

    def __call__(self):
        return self.ahora

    def avanzar(self, minutos):
        self.ahora += timedelta(minutes=minutos)


@pytest.fixture
def reloj():
    return Reloj(datetime(2026, 10, 10, 8, 0, tzinfo=timezone.utc))


@pytest.fixture
def db():
    base = mongomock.MongoClient().gestlab_pruebas
    crear_indices(base)
    return base


@pytest.fixture
def repos(db):
    return SimpleNamespace(
        actividades=ActividadRepository(db),
        asignaciones=AsignacionRepository(db),
        catalogos=CatalogoRepository(db),
        ejecuciones=EjecucionRepository(db),
        empresas=EmpresaRepository(db),
        proyectos=ProyectoRepository(db),
        requerimientos=RequerimientoRepository(db),
        usuarios=UsuarioRepository(db),
    )


@pytest.fixture
def servicios(db, reloj):
    """Los mismos servicios de la aplicación (actividades, ejecucion, carga, proyectos y catalogos),
    armados igual que en las rutas pero con el reloj de la prueba."""
    return construir_servicios(db, reloj=reloj)


def _crear_usuario(repos, empresa_id, nombre, rol):
    usuario_id = repos.usuarios.insert({
        "nombre": nombre, "correo": f"{nombre.lower()}@prueba.co", "rol": rol, "empresa_id": empresa_id,
    })
    # La misma forma que guarda la sesión de Flask (app/utils/seguridad.py).
    return {"id": usuario_id, "nombre": nombre, "rol": rol, "empresa_id": empresa_id}


@pytest.fixture
def empresa(repos):
    """Una empresa con un requerimiento, un administrador (Marta) y dos operarios (Ana y Luis)."""
    empresa_id = repos.empresas.insert({"nombre": "Empresa de prueba", "nit": "900", "consecutivo_actividad": 0})
    requerimiento_id = repos.requerimientos.insert({"titulo": "General", "empresa_id": empresa_id})
    return SimpleNamespace(
        id=empresa_id,
        requerimiento_id=requerimiento_id,
        admin=_crear_usuario(repos, empresa_id, "Marta", "ADMINISTRADOR"),
        ana=_crear_usuario(repos, empresa_id, "Ana", "OPERARIO"),
        luis=_crear_usuario(repos, empresa_id, "Luis", "OPERARIO"),
    )


@pytest.fixture
def otra_empresa(repos):
    """Una segunda empresa, con su administrador (Rosa) y un operario (Iván)."""
    empresa_id = repos.empresas.insert({"nombre": "Otra empresa", "nit": "901", "consecutivo_actividad": 0})
    return SimpleNamespace(
        id=empresa_id,
        admin=_crear_usuario(repos, empresa_id, "Rosa", "ADMINISTRADOR"),
        ivan=_crear_usuario(repos, empresa_id, "Ivan", "OPERARIO"),
    )


@pytest.fixture
def crear_actividad(servicios, empresa):
    """Crea una actividad como lo hace el Administrador y la devuelve ya presentada."""
    def _crear(operarios, titulo="Calibrar la selladora", **campos):
        datos = {
            "titulo": titulo,
            "ubicacion": "Línea 2",
            "requerimiento_id": empresa.requerimiento_id,
            "categoria": "MANTENIMIENTO",
            "prioridad": "MEDIA",
            "tiempo_estimado_min": 60,
            "fecha_programada": HOY,
            "operario_ids": [operario["id"] for operario in operarios],
            **campos,
        }
        return servicios.actividades.crear_actividad(datos, empresa.admin)
    return _crear


@pytest.fixture
def cliente_de(db, reloj):
    """Devuelve un cliente HTTP con la sesión de ese usuario ya iniciada (o sin sesión, con None).
    Monta las rutas de actividades, proyectos, carga, programación del día, catálogos, usuarios, turnos
    y asistencia sobre la base en memoria, con el mismo
    manejador de errores de app/__init__.py (create_app se conectaría a MongoDB)."""
    from flask import Flask, jsonify

    from app.routes.actividad_routes import create_blueprint as actividad_bp
    from app.routes.analisis_routes import create_blueprint as analisis_bp
    from app.routes.asistencia_routes import create_blueprint as asistencia_bp
    from app.routes.catalogo_routes import create_blueprint as catalogo_bp
    from app.routes.programacion_routes import create_blueprint as programacion_bp
    from app.routes.proyecto_routes import create_blueprint as proyecto_bp
    from app.routes.turno_routes import create_blueprint as turno_bp
    from app.routes.usuario_routes import create_blueprint as usuario_bp
    from app.utils.errors import ErrorApi

    app = Flask(__name__)
    app.config.update(SECRET_KEY="pruebas", TESTING=True)
    # Con el reloj de la prueba: con la hora real, el cierre de jornada reprogramaría las actividades
    # de HOY en cuanto pasara esa fecha.
    for blueprint in (actividad_bp, proyecto_bp, analisis_bp, programacion_bp, usuario_bp, turno_bp, asistencia_bp):
        app.register_blueprint(blueprint(db, reloj=reloj))
    app.register_blueprint(catalogo_bp(db))

    @app.errorhandler(ErrorApi)
    def manejar_error_api(error):
        return jsonify({"error": str(error)}), error.status_code

    def _cliente(usuario=None):
        cliente = app.test_client()
        if usuario:
            with cliente.session_transaction() as sesion:
                sesion["usuario"] = usuario
        return cliente
    return _cliente
