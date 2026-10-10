from flask import Blueprint, jsonify, request

from app.models.enums import Rol
from app.services.composicion import construir_servicios
from app.utils.seguridad import requiere_rol, usuario_actual


def create_blueprint(db, reloj=None):
    """Asistencia: el Operario marca entrada y salida (/asistencia/...); el Administrador revisa,
    valida y corrige las de su empresa (/asistencias/...). La hora de cada marca la pone el servidor.
    Con "reloj" las pruebas controlan la hora; sin él, los servicios usan la del servidor."""
    bp = Blueprint("asistencia", __name__)
    service = construir_servicios(db, reloj=reloj).asistencia

    # ---------- Operario ----------

    @bp.post("/asistencia/entrada")
    @requiere_rol(Rol.OPERARIO)
    def marcar_entrada():
        return jsonify(service.marcar_entrada(usuario_actual())), 201

    @bp.post("/asistencia/salida")
    @requiere_rol(Rol.OPERARIO)
    def marcar_salida():
        return jsonify(service.marcar_salida(usuario_actual())), 200

    @bp.get("/asistencia/hoy")
    @requiere_rol(Rol.OPERARIO)
    def consultar_hoy():
        return jsonify(service.consultar_hoy(usuario_actual())), 200

    # ---------- Administrador ----------

    @bp.get("/asistencias")
    @requiere_rol(Rol.ADMINISTRADOR)
    def listar():
        """Las de una jornada (?jornada=AAAA-MM-DD; por defecto, hoy)."""
        return jsonify(service.listar(usuario_actual(), request.args.get("jornada"))), 200

    @bp.post("/asistencias/<asistencia_id>/validar")
    @requiere_rol(Rol.ADMINISTRADOR)
    def validar(asistencia_id):
        return jsonify(service.validar(usuario_actual(), asistencia_id)), 200

    @bp.post("/asistencias/<asistencia_id>/corregir")
    @requiere_rol(Rol.ADMINISTRADOR)
    def corregir(asistencia_id):
        """{"entrada": "HH:MM", "salida": "HH:MM" | null, "motivo": "..."} en la hora de la empresa."""
        data = request.get_json(force=True, silent=True)
        data = data if isinstance(data, dict) else {}
        corregida = service.corregir(usuario_actual(), asistencia_id, data.get("entrada"), data.get("salida"),
                                     data.get("motivo"))
        return jsonify(corregida), 200

    return bp
