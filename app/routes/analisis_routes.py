from flask import Blueprint, jsonify, request

from app.models.enums import Rol
from app.repositories.actividad_repository import ActividadRepository
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.carga_service import CargaService
from app.utils.seguridad import requiere_rol, usuario_actual


def create_blueprint(db):
    bp = Blueprint("analisis", __name__, url_prefix="/analisis")
    carga_service = CargaService(ActividadRepository(db), AsignacionRepository(db), UsuarioRepository(db))

    @bp.get("/carga")
    @requiere_rol(Rol.ADMINISTRADOR, Rol.OPERARIO)
    def carga_por_jornada():
        """Carga laboral por jornada entre dos fechas (?desde=AAAA-MM-DD&hasta=AAAA-MM-DD)."""
        carga = carga_service.consultar(request.args.get("desde"), request.args.get("hasta"), usuario_actual())
        return jsonify(carga), 200

    return bp
