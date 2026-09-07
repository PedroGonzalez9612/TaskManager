from flask import Blueprint, jsonify, request

from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.usuario_service import UsuarioService


def create_blueprint(db):
    bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")
    service = UsuarioService(UsuarioRepository(db), EmpresaRepository(db))

    @bp.post("")
    def crear_usuario():
        usuario = service.crear_usuario(request.get_json(force=True, silent=True) or {})
        return jsonify(usuario), 201

    @bp.get("")
    def listar_usuarios():
        empresa_id = request.args.get("empresa_id")
        return jsonify(service.listar_usuarios(empresa_id)), 200

    @bp.get("/<usuario_id>")
    def obtener_usuario(usuario_id):
        return jsonify(service.obtener_usuario(usuario_id)), 200

    @bp.put("/<usuario_id>")
    def actualizar_usuario(usuario_id):
        usuario = service.actualizar_usuario(usuario_id, request.get_json(force=True, silent=True) or {})
        return jsonify(usuario), 200

    @bp.delete("/<usuario_id>")
    def eliminar_usuario(usuario_id):
        service.eliminar_usuario(usuario_id)
        return "", 204

    return bp
