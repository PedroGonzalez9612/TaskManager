from flask import Blueprint, jsonify, request

from app.repositories.empresa_repository import EmpresaRepository
from app.services.empresa_service import EmpresaService


def create_blueprint(db):
    bp = Blueprint("empresas", __name__, url_prefix="/empresas")
    service = EmpresaService(EmpresaRepository(db))

    @bp.post("")
    def crear_empresa():
        empresa = service.crear_empresa(request.get_json(force=True, silent=True) or {})
        return jsonify(empresa), 201

    @bp.get("")
    def listar_empresas():
        return jsonify(service.listar_empresas()), 200

    @bp.get("/<empresa_id>")
    def obtener_empresa(empresa_id):
        return jsonify(service.obtener_empresa(empresa_id)), 200

    @bp.put("/<empresa_id>")
    def actualizar_empresa(empresa_id):
        empresa = service.actualizar_empresa(empresa_id, request.get_json(force=True, silent=True) or {})
        return jsonify(empresa), 200

    @bp.delete("/<empresa_id>")
    def eliminar_empresa(empresa_id):
        service.eliminar_empresa(empresa_id)
        return "", 204

    return bp
