from flask import Blueprint, jsonify, request

from app.repositories.actividad_repository import ActividadRepository
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.asignacion_service import AsignacionService


def create_blueprint(db):
    bp = Blueprint("asignaciones", __name__, url_prefix="/asignaciones")
    service = AsignacionService(AsignacionRepository(db), ActividadRepository(db), UsuarioRepository(db))

    @bp.post("")
    def crear_asignacion():
        asignacion = service.asignar(request.get_json(force=True, silent=True) or {})
        return jsonify(asignacion), 200

    @bp.get("")
    def listar_asignaciones_por_usuario():
        usuario_id = request.args.get("usuario_id")
        if not usuario_id:
            return jsonify([]), 200
        return jsonify(service.listar_por_usuario(usuario_id)), 200

    @bp.delete("/<asignacion_id>")
    def eliminar_asignacion(asignacion_id):
        service.eliminar_asignacion(asignacion_id)
        return "", 204

    return bp
