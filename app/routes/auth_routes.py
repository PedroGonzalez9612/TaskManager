from flask import Blueprint, jsonify, request, session

from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.auth_service import AuthService
from app.services.empresa_service import EmpresaService
from app.utils.seguridad import guardar_sesion, requiere_rol, usuario_actual


def create_blueprint(db):
    bp = Blueprint("auth", __name__, url_prefix="/auth")
    service = AuthService(UsuarioRepository(db))
    empresa_service = EmpresaService(EmpresaRepository(db), UsuarioRepository(db))

    @bp.post("/login")
    def iniciar_sesion():
        data = request.get_json(force=True, silent=True) or {}
        usuario = service.iniciar_sesion(data.get("correo"), data.get("contraseña"))
        guardar_sesion(usuario)
        return jsonify(usuario), 200

    @bp.post("/logout")
    def cerrar_sesion():
        session.clear()
        return "", 204

    @bp.get("/sesion")
    @requiere_rol()
    def sesion_actual():
        usuario = dict(usuario_actual())
        # Nombre y logo de la empresa, para mostrar su marca en el menú (marca blanca).
        usuario["empresa"] = None
        if usuario["empresa_id"]:
            empresa = empresa_service.obtener_empresa(usuario["empresa_id"])
            usuario["empresa"] = {"nombre": empresa["nombre"], "tiene_logo": empresa["tiene_logo"]}
        return jsonify(usuario), 200

    return bp
