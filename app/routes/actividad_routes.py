from flask import Blueprint, jsonify, request

from app.repositories.actividad_repository import ActividadRepository
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.ejecucion_repository import EjecucionRepository
from app.repositories.registro_tiempo_repository import RegistroTiempoRepository
from app.repositories.requerimiento_repository import RequerimientoRepository
from app.services.actividad_service import ActividadService
from app.services.asignacion_service import AsignacionService
from app.services.ejecucion_service import EjecucionService
from app.services.registro_tiempo_service import RegistroTiempoService
from app.repositories.usuario_repository import UsuarioRepository


def create_blueprint(db):
    bp = Blueprint("actividades", __name__, url_prefix="/actividades")
    actividad_repository = ActividadRepository(db)
    asignacion_repository = AsignacionRepository(db)
    ejecucion_repository = EjecucionRepository(db)
    registro_tiempo_repository = RegistroTiempoRepository(db)

    service = ActividadService(actividad_repository, RequerimientoRepository(db))
    asignacion_service = AsignacionService(asignacion_repository, actividad_repository, UsuarioRepository(db))
    ejecucion_service = EjecucionService(ejecucion_repository, actividad_repository, asignacion_repository)
    registro_tiempo_service = RegistroTiempoService(
        registro_tiempo_repository, actividad_repository, UsuarioRepository(db)
    )

    @bp.post("")
    def crear_actividad():
        actividad = service.crear_actividad(request.get_json(force=True, silent=True) or {})
        return jsonify(actividad), 201

    @bp.get("")
    def listar_actividades():
        requerimiento_id = request.args.get("requerimiento_id")
        return jsonify(service.listar_actividades(requerimiento_id)), 200

    @bp.get("/<actividad_id>")
    def obtener_actividad(actividad_id):
        return jsonify(service.obtener_actividad(actividad_id)), 200

    @bp.put("/<actividad_id>")
    def actualizar_actividad(actividad_id):
        actividad = service.actualizar_actividad(actividad_id, request.get_json(force=True, silent=True) or {})
        return jsonify(actividad), 200

    @bp.delete("/<actividad_id>")
    def eliminar_actividad(actividad_id):
        service.eliminar_actividad(actividad_id)
        return "", 204

    @bp.post("/<actividad_id>/asignar")
    def asignar_actividad(actividad_id):
        data = request.get_json(force=True, silent=True) or {}
        data["actividad_id"] = actividad_id
        asignacion = asignacion_service.asignar(data)
        return jsonify(asignacion), 200

    @bp.get("/<actividad_id>/asignacion")
    def obtener_asignacion(actividad_id):
        return jsonify(asignacion_service.obtener_por_actividad(actividad_id)), 200

    @bp.post("/<actividad_id>/iniciar")
    def iniciar_ejecucion(actividad_id):
        return jsonify(ejecucion_service.iniciar(actividad_id)), 200

    @bp.post("/<actividad_id>/finalizar")
    def finalizar_ejecucion(actividad_id):
        return jsonify(ejecucion_service.finalizar(actividad_id)), 200

    @bp.get("/<actividad_id>/ejecucion")
    def obtener_ejecucion(actividad_id):
        return jsonify(ejecucion_service.obtener_por_actividad(actividad_id)), 200

    @bp.post("/<actividad_id>/registros-tiempo")
    def registrar_tiempo(actividad_id):
        data = request.get_json(force=True, silent=True) or {}
        data["actividad_id"] = actividad_id
        registro = registro_tiempo_service.registrar_tiempo(data)
        return jsonify(registro), 201

    @bp.get("/<actividad_id>/registros-tiempo")
    def listar_registros_tiempo(actividad_id):
        return jsonify(registro_tiempo_service.listar_por_actividad(actividad_id)), 200

    return bp
