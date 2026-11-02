from flask import Blueprint, jsonify

from app.models.enums import Rol
from app.services.composicion import construir_servicios
from app.utils.seguridad import requiere_rol, usuario_actual


def create_blueprint(db, reloj=None):
    """La pantalla Hoy del Administrador (alcance, Sección 6.2). Con "reloj" las pruebas controlan la hora."""
    bp = Blueprint("hoy", __name__, url_prefix="/hoy")
    service = construir_servicios(db, reloj=reloj).hoy

    @bp.get("/personas")
    @requiere_rol(Rol.ADMINISTRADOR)
    def personas():
        """Cada operario con su presencia, lo que hace y su carga de la jornada."""
        return jsonify(service.personas(usuario_actual())), 200

    @bp.get("/pendientes")
    @requiere_rol(Rol.ADMINISTRADOR)
    def pendientes():
        """Lo que pide una decisión del Administrador, agrupado de lo más urgente a lo menos."""
        return jsonify(service.pendientes(usuario_actual())), 200

    return bp
