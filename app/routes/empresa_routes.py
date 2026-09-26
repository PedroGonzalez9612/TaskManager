from flask import Blueprint, Response, jsonify, request

from app.models.enums import Rol
from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.empresa_service import EmpresaService
from app.utils.seguridad import requiere_rol, usuario_actual


def create_blueprint(db):
    bp = Blueprint("empresas", __name__, url_prefix="/empresas")
    service = EmpresaService(EmpresaRepository(db), UsuarioRepository(db))

    @bp.post("")
    @requiere_rol(Rol.SUPERADMIN)
    def crear_empresa():
        empresa = service.crear_empresa(request.get_json(force=True, silent=True) or {})
        return jsonify(empresa), 201

    @bp.get("")
    @requiere_rol(Rol.SUPERADMIN)
    def listar_empresas():
        return jsonify(service.listar_empresas()), 200

    @bp.get("/<empresa_id>")
    @requiere_rol(Rol.SUPERADMIN, Rol.ADMINISTRADOR)
    def obtener_empresa(empresa_id):
        return jsonify(service.obtener_empresa(empresa_id, usuario_actual())), 200

    @bp.put("/<empresa_id>")
    @requiere_rol(Rol.SUPERADMIN)
    def actualizar_empresa(empresa_id):
        empresa = service.actualizar_empresa(empresa_id, request.get_json(force=True, silent=True) or {})
        return jsonify(empresa), 200

    @bp.put("/<empresa_id>/logo")
    @requiere_rol(Rol.SUPERADMIN)
    def subir_logo(empresa_id):
        # El logo llega como archivo (multipart/form-data), no como JSON.
        archivo = request.files.get("logo")
        contenido = archivo.read() if archivo else b""
        return jsonify(service.guardar_logo(empresa_id, contenido)), 200

    @bp.get("/<empresa_id>/logo")
    @requiere_rol()
    def obtener_logo(empresa_id):
        contenido, tipo = service.obtener_logo(empresa_id, usuario_actual())
        respuesta = Response(contenido, mimetype=tipo)
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        respuesta.headers["Cache-Control"] = "private, max-age=300"
        return respuesta

    @bp.delete("/<empresa_id>")
    @requiere_rol(Rol.SUPERADMIN)
    def eliminar_empresa(empresa_id):
        service.eliminar_empresa(empresa_id)
        return "", 204

    return bp
