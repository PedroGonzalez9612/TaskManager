from flask import Flask, jsonify

from app.config import Config
from app.extensions import init_db
from app.utils.errors import NotFoundError, ValidationError


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db = init_db(app)

    from app.routes.empresa_routes import create_blueprint as empresa_bp
    from app.routes.usuario_routes import create_blueprint as usuario_bp
    from app.routes.requerimiento_routes import create_blueprint as requerimiento_bp
    from app.routes.actividad_routes import create_blueprint as actividad_bp
    from app.routes.asignacion_routes import create_blueprint as asignacion_bp
    from app.routes.registro_tiempo_routes import create_blueprint as registro_tiempo_bp
    from app.routes.analisis_routes import create_blueprint as analisis_bp

    app.register_blueprint(empresa_bp(db))
    app.register_blueprint(usuario_bp(db))
    app.register_blueprint(requerimiento_bp(db))
    app.register_blueprint(actividad_bp(db))
    app.register_blueprint(asignacion_bp(db))
    app.register_blueprint(registro_tiempo_bp(db))
    app.register_blueprint(analisis_bp(db))

    @app.errorhandler(NotFoundError)
    def handle_not_found(error):
        return jsonify({"error": str(error)}), error.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return jsonify({"error": str(error)}), error.status_code

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app
