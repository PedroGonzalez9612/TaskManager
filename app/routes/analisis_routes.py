from flask import Blueprint, jsonify, request

from app.models.enums import Rol
from app.services.composicion import construir_servicios
from app.utils.seguridad import requiere_rol, usuario_actual


def create_blueprint(db, reloj=None):
    """Con "reloj" las pruebas controlan la hora; sin él, los servicios usan la del servidor."""
    bp = Blueprint("analisis", __name__, url_prefix="/analisis")
    carga_service = construir_servicios(db, reloj=reloj).carga

    @bp.get("/carga")
    @requiere_rol(Rol.ADMINISTRADOR, Rol.OPERARIO)
    def carga_por_jornada():
        """Carga laboral por jornada entre dos fechas (?desde=AAAA-MM-DD&hasta=AAAA-MM-DD)."""
        carga = carga_service.consultar(request.args.get("desde"), request.args.get("hasta"), usuario_actual())
        return jsonify(carga), 200

    return bp
