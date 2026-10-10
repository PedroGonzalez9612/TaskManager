from flask import Blueprint, jsonify, request

from app.models.enums import Rol
from app.services.composicion import construir_servicios
from app.utils.seguridad import requiere_rol, usuario_actual


def create_blueprint(db, reloj=None):
    """Con "reloj" las pruebas controlan la hora; sin él, los servicios usan la del servidor."""
    bp = Blueprint("actividades", __name__, url_prefix="/actividades")
    servicios = construir_servicios(db, reloj=reloj)
    service = servicios.actividades
    ejecucion_service = servicios.ejecucion

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
            "proyecto_id": request.args.get("proyecto_id"),
            "independientes": request.args.get("independientes") in ("1", "true"),
            "sin_asignar": request.args.get("sin_asignar") in ("1", "true"),
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

    @bp.post("/<actividad_id>/cancelar")
    @requiere_rol(Rol.ADMINISTRADOR)
    def cancelar_actividad(actividad_id):
        data = _cuerpo_json()
        return jsonify(service.cancelar(actividad_id, usuario_actual(), data.get("motivo"), data.get("detalle"))), 200

    # Ejecución del operario que tiene la sesión. Las cuatro rutas devuelven la actividad como la
    # ve ese operario (la misma forma de GET /actividades/<id>).

    @bp.post("/<actividad_id>/iniciar")
    @requiere_rol(Rol.OPERARIO)
    def iniciar_ejecucion(actividad_id):
        return jsonify(ejecucion_service.iniciar(actividad_id, usuario_actual())), 200

    @bp.post("/<actividad_id>/pausar")
    @requiere_rol(Rol.OPERARIO)
    def pausar_ejecucion(actividad_id):
        data = _cuerpo_json()
        return jsonify(ejecucion_service.pausar(
            actividad_id, usuario_actual(), data.get("motivo"), data.get("detalle"),
        )), 200

    @bp.post("/<actividad_id>/reanudar")
    @requiere_rol(Rol.OPERARIO)
    def reanudar_ejecucion(actividad_id):
        return jsonify(ejecucion_service.reanudar(actividad_id, usuario_actual())), 200

    @bp.post("/<actividad_id>/finalizar")
    @requiere_rol(Rol.OPERARIO)
    def finalizar_ejecucion(actividad_id):
        data = _cuerpo_json()    # El cuerpo es opcional: se puede finalizar sin observación.
        return jsonify(ejecucion_service.finalizar(actividad_id, usuario_actual(), data.get("observacion"))), 200

    @bp.post("/<actividad_id>/devolver")
    @requiere_rol(Rol.OPERARIO)
    def devolver_actividad(actividad_id):
        # Quien devuelve deja de ver la actividad: la respuesta es la constancia de la devolución.
        data = _cuerpo_json()
        return jsonify(ejecucion_service.devolver(
            actividad_id, usuario_actual(), data.get("motivo"), data.get("detalle"),
        )), 200

    return bp


def _cuerpo_json() -> dict:
    """El cuerpo de la petición como diccionario; vacío si no viene o no es un objeto JSON."""
    data = request.get_json(force=True, silent=True)
    return data if isinstance(data, dict) else {}
