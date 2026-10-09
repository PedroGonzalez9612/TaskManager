from flask import Blueprint, jsonify, request

from app.models.enums import Rol
from app.repositories.actividad_repository import ActividadRepository
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.ejecucion_repository import EjecucionRepository
from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.requerimiento_repository import RequerimientoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.actividad_service import ActividadService
from app.services.carga_service import CargaService
from app.services.ejecucion_service import EjecucionService
from app.utils.seguridad import requiere_rol, usuario_actual


def create_blueprint(db):
    bp = Blueprint("actividades", __name__, url_prefix="/actividades")
    actividad_repository = ActividadRepository(db)
    asignacion_repository = AsignacionRepository(db)
    ejecucion_repository = EjecucionRepository(db)
    usuario_repository = UsuarioRepository(db)

    carga_service = CargaService(actividad_repository, asignacion_repository, usuario_repository)
    service = ActividadService(
        actividad_repository, RequerimientoRepository(db), asignacion_repository,
        usuario_repository, ejecucion_repository, EmpresaRepository(db), carga_service,
    )
    ejecucion_service = EjecucionService(ejecucion_repository, actividad_repository, asignacion_repository)

    @bp.post("")
    @requiere_rol(Rol.ADMINISTRADOR)
    def crear_actividad():
        data = request.get_json(force=True, silent=True) or {}
        return jsonify(service.crear_actividad(data, usuario_actual())), 201

    @bp.get("")
    @requiere_rol(Rol.ADMINISTRADOR, Rol.OPERARIO)
    def listar_actividades():
        filtros = {
            "requerimiento_id": request.args.get("requerimiento_id"),
            "fecha_desde": request.args.get("fecha_desde"),
            "fecha_hasta": request.args.get("fecha_hasta"),
        }
        return jsonify(service.listar_actividades(filtros, usuario_actual())), 200

    @bp.get("/<actividad_id>")
    @requiere_rol(Rol.ADMINISTRADOR, Rol.OPERARIO)
    def obtener_actividad(actividad_id):
        return jsonify(service.obtener_actividad(actividad_id, usuario_actual())), 200

    @bp.put("/<actividad_id>")
    @requiere_rol(Rol.ADMINISTRADOR)
    def actualizar_actividad(actividad_id):
        data = request.get_json(force=True, silent=True) or {}
        return jsonify(service.actualizar_actividad(actividad_id, data, usuario_actual())), 200

    @bp.delete("/<actividad_id>")
    @requiere_rol(Rol.ADMINISTRADOR)
    def eliminar_actividad(actividad_id):
        service.eliminar_actividad(actividad_id, usuario_actual())
        return "", 204

    @bp.post("/<actividad_id>/iniciar")
    @requiere_rol(Rol.OPERARIO)
    def iniciar_ejecucion(actividad_id):
        return jsonify(ejecucion_service.iniciar(actividad_id, usuario_actual())), 200

    @bp.post("/<actividad_id>/finalizar")
    @requiere_rol(Rol.OPERARIO)
    def finalizar_ejecucion(actividad_id):
        return jsonify(ejecucion_service.finalizar(actividad_id, usuario_actual())), 200

    return bp
