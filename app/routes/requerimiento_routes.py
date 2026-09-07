from flask import Blueprint, jsonify, request

from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.requerimiento_repository import RequerimientoRepository
from app.services.requerimiento_service import RequerimientoService


def create_blueprint(db):
    bp = Blueprint("requerimientos", __name__, url_prefix="/requerimientos")
    service = RequerimientoService(RequerimientoRepository(db), EmpresaRepository(db))

    @bp.post("")
    def crear_requerimiento():
        requerimiento = service.crear_requerimiento(request.get_json(force=True, silent=True) or {})
        return jsonify(requerimiento), 201

    @bp.get("")
    def listar_requerimientos():
        empresa_id = request.args.get("empresa_id")
        return jsonify(service.listar_requerimientos(empresa_id)), 200

    @bp.get("/<requerimiento_id>")
    def obtener_requerimiento(requerimiento_id):
        return jsonify(service.obtener_requerimiento(requerimiento_id)), 200

    @bp.put("/<requerimiento_id>")
    def actualizar_requerimiento(requerimiento_id):
        requerimiento = service.actualizar_requerimiento(
            requerimiento_id, request.get_json(force=True, silent=True) or {}
        )
        return jsonify(requerimiento), 200

    @bp.delete("/<requerimiento_id>")
    def eliminar_requerimiento(requerimiento_id):
        service.eliminar_requerimiento(requerimiento_id)
        return "", 204

    return bp
