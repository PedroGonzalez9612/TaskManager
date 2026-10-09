from flask import Flask, jsonify, redirect

from app.config import Config
from app.extensions import init_db
from app.utils.errors import ErrorApi


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db = init_db(app)
    _crear_superadmin_inicial(app, db)

    from app.routes.auth_routes import create_blueprint as auth_bp
    from app.routes.empresa_routes import create_blueprint as empresa_bp
    from app.routes.usuario_routes import create_blueprint as usuario_bp
    from app.routes.requerimiento_routes import create_blueprint as requerimiento_bp
    from app.routes.actividad_routes import create_blueprint as actividad_bp
    from app.routes.analisis_routes import create_blueprint as analisis_bp

    app.register_blueprint(auth_bp(db))
    app.register_blueprint(empresa_bp(db))
    app.register_blueprint(usuario_bp(db))
    app.register_blueprint(requerimiento_bp(db))
    app.register_blueprint(actividad_bp(db))
    app.register_blueprint(analisis_bp(db))

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
