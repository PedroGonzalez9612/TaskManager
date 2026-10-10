from flask import Blueprint, jsonify

from app.models.enums import Rol
from app.services.catalogo_service import MOTIVO_CANCELACION, MOTIVO_DEVOLUCION, MOTIVO_PAUSA
from app.services.composicion import construir_servicios
from app.utils.seguridad import requiere_rol, usuario_actual

# Nombre de cada lista en la dirección (por ejemplo, /catalogos/motivos-pausa).
TIPOS_POR_RUTA = {
    "motivos-pausa": MOTIVO_PAUSA,
    "motivos-cancelacion": MOTIVO_CANCELACION,
    "motivos-devolucion": MOTIVO_DEVOLUCION,
}


def create_blueprint(db):
    bp = Blueprint("catalogos", __name__, url_prefix="/catalogos")
    service = construir_servicios(db).catalogos

    @bp.get("/<tipo>")
    @requiere_rol(Rol.ADMINISTRADOR, Rol.OPERARIO)
    def listar_catalogo(tipo):
        # Si el nombre no corresponde a ninguna lista, el servicio responde que no existe (404).
        return jsonify(service.listar(usuario_actual(), TIPOS_POR_RUTA.get(tipo))), 200

    return bp
