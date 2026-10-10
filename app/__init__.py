from flask import Flask, jsonify, redirect

from app.config import Config
from app.extensions import init_db
from app.utils.errors import ErrorApi
from app.utils.seguridad import exigir_peticion_propia


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    # Protección contra CSRF: ver app/utils/seguridad.py.
    app.before_request(exigir_peticion_propia)

    db = init_db(app)
    _crear_indices(app, db)
    _crear_superadmin_inicial(app, db)

    from app.routes.auth_routes import create_blueprint as auth_bp
    from app.routes.empresa_routes import create_blueprint as empresa_bp
    from app.routes.usuario_routes import create_blueprint as usuario_bp
    from app.routes.requerimiento_routes import create_blueprint as requerimiento_bp
    from app.routes.actividad_routes import create_blueprint as actividad_bp
    from app.routes.analisis_routes import create_blueprint as analisis_bp
    from app.routes.proyecto_routes import create_blueprint as proyecto_bp
    from app.routes.catalogo_routes import create_blueprint as catalogo_bp
    from app.routes.programacion_routes import create_blueprint as programacion_bp
    from app.routes.turno_routes import create_blueprint as turno_bp
    from app.routes.asistencia_routes import create_blueprint as asistencia_bp

    app.register_blueprint(auth_bp(db))
    app.register_blueprint(empresa_bp(db))
    app.register_blueprint(usuario_bp(db))
    app.register_blueprint(requerimiento_bp(db))
    app.register_blueprint(actividad_bp(db))
    app.register_blueprint(analisis_bp(db))
    app.register_blueprint(proyecto_bp(db))
    app.register_blueprint(catalogo_bp(db))
    app.register_blueprint(programacion_bp(db))
    app.register_blueprint(turno_bp(db))
    app.register_blueprint(asistencia_bp(db))

    @app.errorhandler(ErrorApi)
    def handle_error_api(error):
        return jsonify({"error": str(error)}), error.status_code

    @app.errorhandler(413)
    def handle_archivo_muy_grande(error):
        return jsonify({"error": "El archivo es demasiado grande"}), 413

    @app.get("/")
    def inicio():
        return redirect("/static/login.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app


def _crear_indices(app, db):
    """Si un índice no se puede crear (por ejemplo, datos anteriores que lo incumplen), la aplicación
    arranca igual y lo avisa: se corrige con herramientas/migrar_etapa4.py."""
    from pymongo.errors import OperationFailure

    from app.repositories import crear_indices

    try:
        crear_indices(db)
    except OperationFailure as error:
        app.logger.warning("No se pudieron crear todos los índices de MongoDB: %s", error)


def _crear_superadmin_inicial(app, db):
    from app.repositories.usuario_repository import UsuarioRepository
    from app.services.auth_service import AuthService

    creado = AuthService(UsuarioRepository(db)).crear_superadmin_inicial(
        app.config["SUPERADMIN_NOMBRE"],
        app.config["SUPERADMIN_CORREO"],
        app.config["SUPERADMIN_CONTRASENA"],
    )
    if creado:
        app.logger.warning("Se creó el Superadmin inicial con el correo %s", app.config["SUPERADMIN_CORREO"])
