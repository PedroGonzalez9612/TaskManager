from flask import Blueprint, jsonify, request

from app.repositories.actividad_repository import ActividadRepository
from app.repositories.registro_tiempo_repository import RegistroTiempoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.registro_tiempo_service import RegistroTiempoService


def create_blueprint(db):
    bp = Blueprint("registros_tiempo", __name__, url_prefix="/registros-tiempo")
    service = RegistroTiempoService(RegistroTiempoRepository(db), ActividadRepository(db), UsuarioRepository(db))

    @bp.post("")
    def crear_registro():
        registro = service.registrar_tiempo(request.get_json(force=True, silent=True) or {})
        return jsonify(registro), 201

    @bp.get("")
    def listar_registros():
        usuario_id = request.args.get("usuario_id")
        actividad_id = request.args.get("actividad_id")
        if usuario_id:
            return jsonify(service.listar_por_usuario(usuario_id)), 200
        if actividad_id:
            return jsonify(service.listar_por_actividad(actividad_id)), 200
        return jsonify([]), 200

    @bp.delete("/<registro_id>")
    def eliminar_registro(registro_id):
        service.eliminar_registro(registro_id)
        return "", 204

    return bp
