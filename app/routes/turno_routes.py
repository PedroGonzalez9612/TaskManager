from flask import Blueprint, jsonify, request

from app.models.enums import Rol
from app.services.composicion import construir_servicios
from app.utils.seguridad import requiere_rol, usuario_actual


def create_blueprint(db, reloj=None):
    """Catálogo de turnos de la empresa. El turno de cada operario se asigna en PUT /usuarios/<id>/turno.
    Con "reloj" las pruebas controlan la hora; sin él, los servicios usan la del servidor."""
    bp = Blueprint("turnos", __name__, url_prefix="/turnos")
    service = construir_servicios(db, reloj=reloj).turnos

    @bp.post("")
    @requiere_rol(Rol.ADMINISTRADOR)
    def crear_turno():
        return jsonify(service.crear_turno(_cuerpo_json(), usuario_actual())), 201

    @bp.get("")
    @requiere_rol(Rol.ADMINISTRADOR)
    def listar_turnos():
        return jsonify(service.listar_turnos(usuario_actual())), 200

    @bp.put("/<turno_id>")
    @requiere_rol(Rol.ADMINISTRADOR)
    def editar_turno(turno_id):
        return jsonify(service.editar_turno(turno_id, _cuerpo_json(), usuario_actual())), 200

    return bp


def _cuerpo_json() -> dict:
    """El cuerpo de la petición como diccionario; vacío si no viene o no es un objeto JSON."""
    data = request.get_json(force=True, silent=True)
    return data if isinstance(data, dict) else {}
