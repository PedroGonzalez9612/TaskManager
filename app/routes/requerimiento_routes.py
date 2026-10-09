from flask import Blueprint, jsonify, request

from app.models.enums import Rol
from app.repositories.actividad_repository import ActividadRepository
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.ejecucion_repository import EjecucionRepository
from app.repositories.requerimiento_repository import RequerimientoRepository
from app.services.requerimiento_service import RequerimientoService
from app.utils.seguridad import requiere_rol, usuario_actual


def create_blueprint(db):
    bp = Blueprint("requerimientos", __name__, url_prefix="/requerimientos")
    service = RequerimientoService(
        RequerimientoRepository(db), ActividadRepository(db), AsignacionRepository(db), EjecucionRepository(db)
    )

    @bp.post("")
    @requiere_rol(Rol.ADMINISTRADOR)
    def crear_requerimiento():
        data = request.get_json(force=True, silent=True) or {}
        return jsonify(service.crear_requerimiento(data, usuario_actual())), 201

    @bp.get("")
    @requiere_rol(Rol.ADMINISTRADOR)
    def listar_requerimientos():
        return jsonify(service.listar_requerimientos(usuario_actual())), 200

    @bp.get("/<requerimiento_id>")
    @requiere_rol(Rol.ADMINISTRADOR)
    def obtener_requerimiento(requerimiento_id):
        return jsonify(service.obtener_requerimiento(requerimiento_id, usuario_actual())), 200

    @bp.put("/<requerimiento_id>")
    @requiere_rol(Rol.ADMINISTRADOR)
    def actualizar_requerimiento(requerimiento_id):
        data = request.get_json(force=True, silent=True) or {}
        return jsonify(service.actualizar_requerimiento(requerimiento_id, data, usuario_actual())), 200

    @bp.delete("/<requerimiento_id>")
    @requiere_rol(Rol.ADMINISTRADOR)
    def eliminar_requerimiento(requerimiento_id):
        service.eliminar_requerimiento(requerimiento_id, usuario_actual())
        return "", 204

    return bp
