from flask import Blueprint, jsonify, request

from app.models.enums import Rol
from app.repositories.actividad_repository import ActividadRepository
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.composicion import construir_servicios
from app.services.usuario_service import UsuarioService
from app.utils.seguridad import requiere_rol, usuario_actual


def create_blueprint(db, reloj=None):
    """Con "reloj" las pruebas controlan la hora; sin él, los servicios usan la del servidor."""
    bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")
    turno_service = construir_servicios(db, reloj=reloj).turnos
    service = UsuarioService(UsuarioRepository(db), EmpresaRepository(db), turno_service,
                             AsignacionRepository(db), ActividadRepository(db))

    @bp.post("")
    @requiere_rol(Rol.SUPERADMIN, Rol.ADMINISTRADOR)
    def crear_usuario():
        data = request.get_json(force=True, silent=True) or {}
        return jsonify(service.crear_usuario(data, usuario_actual())), 201

    @bp.get("")
    @requiere_rol(Rol.SUPERADMIN, Rol.ADMINISTRADOR)
    def listar_usuarios():
        empresa_id = request.args.get("empresa_id")
        return jsonify(service.listar_usuarios(empresa_id, usuario_actual())), 200

    @bp.get("/<usuario_id>")
    @requiere_rol(Rol.SUPERADMIN, Rol.ADMINISTRADOR)
    def obtener_usuario(usuario_id):
        return jsonify(service.obtener_usuario(usuario_id, usuario_actual())), 200

    @bp.put("/<usuario_id>")
    @requiere_rol(Rol.SUPERADMIN, Rol.ADMINISTRADOR)
    def actualizar_usuario(usuario_id):
        data = request.get_json(force=True, silent=True) or {}
        return jsonify(service.actualizar_usuario(usuario_id, data, usuario_actual())), 200

    @bp.put("/<usuario_id>/turno")
    @requiere_rol(Rol.ADMINISTRADOR)
    def asignar_turno(usuario_id):
        """Asigna un turno al operario desde una fecha: {"turno_id": "...", "desde": "AAAA-MM-DD"?}."""
        data = request.get_json(force=True, silent=True)
        data = data if isinstance(data, dict) else {}
        asignacion = turno_service.asignar_turno(usuario_actual(), usuario_id, data.get("turno_id"), data.get("desde"))
        return jsonify(asignacion), 200

    # Un usuario no se borra: se desactiva y se puede reactivar (alcance, Sección 4).
    @bp.post("/<usuario_id>/desactivar")
    @requiere_rol(Rol.SUPERADMIN, Rol.ADMINISTRADOR)
    def desactivar_usuario(usuario_id):
        return jsonify(service.desactivar_usuario(usuario_id, usuario_actual())), 200

    @bp.post("/<usuario_id>/reactivar")
    @requiere_rol(Rol.SUPERADMIN, Rol.ADMINISTRADOR)
    def reactivar_usuario(usuario_id):
        return jsonify(service.reactivar_usuario(usuario_id, usuario_actual())), 200

    return bp
