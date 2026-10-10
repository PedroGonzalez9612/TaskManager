from flask import Blueprint, jsonify, request

from app.models.enums import Rol
from app.services.composicion import construir_servicios
from app.utils.seguridad import requiere_rol, usuario_actual


def create_blueprint(db, reloj=None):
    """Programación del día y orden del día. Las tres rutas responden con la programación de hoy.
    Con "reloj" las pruebas controlan la hora; sin él, los servicios usan la del servidor."""
    bp = Blueprint("programacion", __name__)
    service = construir_servicios(db, reloj=reloj).programacion

    @bp.get("/programacion-del-dia")
    @requiere_rol(Rol.ADMINISTRADOR, Rol.OPERARIO)
    def consultar_programacion():
        """El Operario ve la suya; el Administrador indica el operario con ?operario_id=..."""
        return jsonify(service.consultar(usuario_actual(), request.args.get("operario_id"))), 200

    @bp.put("/orden-del-dia")
    @requiere_rol(Rol.OPERARIO)
    def guardar_orden():
        data = request.get_json(force=True, silent=True)
        actividad_ids = data.get("actividad_ids") if isinstance(data, dict) else None
        return jsonify(service.guardar_orden(usuario_actual(), actividad_ids)), 200

    @bp.delete("/orden-del-dia")
    @requiere_rol(Rol.OPERARIO)
    def restablecer_orden():
        return jsonify(service.restablecer_orden(usuario_actual())), 200

    return bp
