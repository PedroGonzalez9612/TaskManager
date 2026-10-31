from flask import Blueprint, jsonify, request

from app.models.enums import Rol
from app.services.composicion import construir_servicios
from app.utils.seguridad import requiere_rol, usuario_actual


def create_blueprint(db, reloj=None):
    """Reportes de actividad (alcance, Sección 5.1). Con "reloj" las pruebas controlan la hora."""
    bp = Blueprint("reportes", __name__, url_prefix="/reportes")
    service = construir_servicios(db, reloj=reloj).reportes

    @bp.post("")
    @requiere_rol(Rol.OPERARIO)
    def reportar():
        data = request.get_json(force=True, silent=True) or {}
        return jsonify(service.reportar(data, usuario_actual())), 201

    @bp.get("")
    @requiere_rol(Rol.ADMINISTRADOR, Rol.OPERARIO)
    def listar():
        """El Administrador ve los de su empresa (?estado=PENDIENTE para los por revisar); el Operario, los suyos."""
        return jsonify(service.listar(usuario_actual(), request.args.get("estado"))), 200

    @bp.post("/<reporte_id>/convertir")
    @requiere_rol(Rol.ADMINISTRADOR)
    def convertir(reporte_id):
        """El cuerpo son los datos de la actividad, como al crearla. Devuelve la actividad creada."""
        data = request.get_json(force=True, silent=True) or {}
        return jsonify(service.convertir(reporte_id, data, usuario_actual())), 201

    @bp.post("/<reporte_id>/descartar")
    @requiere_rol(Rol.ADMINISTRADOR)
    def descartar(reporte_id):
        data = request.get_json(force=True, silent=True) or {}
        return jsonify(service.descartar(reporte_id, data.get("motivo"), usuario_actual())), 200

    return bp
