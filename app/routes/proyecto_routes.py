from flask import Blueprint, jsonify, request

from app.models.enums import Rol
from app.services.composicion import construir_servicios
from app.utils.seguridad import requiere_rol, usuario_actual


def create_blueprint(db, reloj=None):
    """Con "reloj" las pruebas controlan la hora; sin él, los servicios usan la del servidor."""
    bp = Blueprint("proyectos", __name__, url_prefix="/proyectos")
    service = construir_servicios(db, reloj=reloj).proyectos

    @bp.post("")
    @requiere_rol(Rol.ADMINISTRADOR)
    def crear_proyecto():
        return jsonify(service.crear_proyecto(_cuerpo_json(), usuario_actual())), 201

    @bp.get("")
    @requiere_rol(Rol.ADMINISTRADOR)
    def listar_proyectos():
        return jsonify(service.listar_proyectos(usuario_actual())), 200

    @bp.get("/<proyecto_id>")
    @requiere_rol(Rol.ADMINISTRADOR)
    def obtener_proyecto(proyecto_id):
        return jsonify(service.obtener_proyecto(proyecto_id, usuario_actual())), 200

    @bp.put("/<proyecto_id>")
    @requiere_rol(Rol.ADMINISTRADOR)
    def actualizar_proyecto(proyecto_id):
        return jsonify(service.actualizar_proyecto(proyecto_id, _cuerpo_json(), usuario_actual())), 200

    return bp


def _cuerpo_json() -> dict:
    """El cuerpo de la petición como diccionario; vacío si no viene o no es un objeto JSON."""
    data = request.get_json(force=True, silent=True)
    return data if isinstance(data, dict) else {}
