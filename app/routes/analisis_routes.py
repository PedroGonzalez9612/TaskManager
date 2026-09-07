from flask import Blueprint, jsonify, request

from app.repositories.actividad_repository import ActividadRepository
from app.repositories.registro_tiempo_repository import RegistroTiempoRepository
from app.repositories.requerimiento_repository import RequerimientoRepository
from app.services.analisis_service import AnalisisService


def create_blueprint(db):
    bp = Blueprint("analisis", __name__, url_prefix="/analisis")
    service = AnalisisService(
        ActividadRepository(db), RequerimientoRepository(db), RegistroTiempoRepository(db)
    )

    @bp.get("/horas-por-actividad")
    def horas_por_actividad():
        return jsonify(service.horas_por_actividad()), 200

    @bp.get("/horas-por-usuario")
    def horas_por_usuario():
        return jsonify(service.horas_por_usuario()), 200

    @bp.get("/actividades-por-estado")
    def actividades_por_estado():
        requerimiento_id = request.args.get("requerimiento_id")
        return jsonify(service.actividades_por_estado(requerimiento_id)), 200

    @bp.get("/requerimientos/<requerimiento_id>/resumen")
    def resumen_requerimiento(requerimiento_id):
        return jsonify(service.resumen_requerimiento(requerimiento_id)), 200

    return bp
