from urllib.parse import quote

from flask import Blueprint, Response, jsonify, request

from app.models.enums import Rol
from app.services.composicion import construir_servicios
from app.utils.seguridad import requiere_rol, usuario_actual


def create_blueprint(db, reloj=None):
    """Con "reloj" las pruebas controlan la hora; sin él, los servicios usan la del servidor."""
    bp = Blueprint("actividades", __name__, url_prefix="/actividades")
    servicios = construir_servicios(db, reloj=reloj)
    service = servicios.actividades
    ejecucion_service = servicios.ejecucion
    evidencia_service = servicios.evidencias
    adjunto_service = servicios.adjuntos

    @bp.post("")
    @requiere_rol(Rol.ADMINISTRADOR)
    def crear_actividad():
        data = request.get_json(force=True, silent=True) or {}
        return jsonify(service.crear_actividad(data, usuario_actual())), 201

    @bp.get("")
    @requiere_rol(Rol.ADMINISTRADOR, Rol.OPERARIO)
    def listar_actividades():
        filtros = {
            "requerimiento_id": request.args.get("requerimiento_id"),
            "fecha_desde": request.args.get("fecha_desde"),
            "fecha_hasta": request.args.get("fecha_hasta"),
            "proyecto_id": request.args.get("proyecto_id"),
            "independientes": request.args.get("independientes") in ("1", "true"),
            "sin_asignar": request.args.get("sin_asignar") in ("1", "true"),
        }
        return jsonify(service.listar_actividades(filtros, usuario_actual())), 200

    @bp.get("/<actividad_id>")
    @requiere_rol(Rol.ADMINISTRADOR, Rol.OPERARIO)
    def obtener_actividad(actividad_id):
        return jsonify(service.obtener_actividad(actividad_id, usuario_actual())), 200

    @bp.put("/<actividad_id>")
    @requiere_rol(Rol.ADMINISTRADOR)
    def actualizar_actividad(actividad_id):
        data = request.get_json(force=True, silent=True) or {}
        return jsonify(service.actualizar_actividad(actividad_id, data, usuario_actual())), 200

    @bp.post("/<actividad_id>/cancelar")
    @requiere_rol(Rol.ADMINISTRADOR)
    def cancelar_actividad(actividad_id):
        data = _cuerpo_json()
        return jsonify(service.cancelar(actividad_id, usuario_actual(), data.get("motivo"), data.get("detalle"))), 200

    # Ejecución del operario que tiene la sesión. Las cuatro rutas devuelven la actividad como la
    # ve ese operario (la misma forma de GET /actividades/<id>).

    @bp.post("/<actividad_id>/iniciar")
    @requiere_rol(Rol.OPERARIO)
    def iniciar_ejecucion(actividad_id):
        return jsonify(ejecucion_service.iniciar(actividad_id, usuario_actual())), 200

    @bp.post("/<actividad_id>/pausar")
    @requiere_rol(Rol.OPERARIO)
    def pausar_ejecucion(actividad_id):
        data = _cuerpo_json()
        return jsonify(ejecucion_service.pausar(
            actividad_id, usuario_actual(), data.get("motivo"), data.get("detalle"),
        )), 200

    @bp.post("/<actividad_id>/reanudar")
    @requiere_rol(Rol.OPERARIO)
    def reanudar_ejecucion(actividad_id):
        return jsonify(ejecucion_service.reanudar(actividad_id, usuario_actual())), 200

    @bp.post("/<actividad_id>/finalizar")
    @requiere_rol(Rol.OPERARIO)
    def finalizar_ejecucion(actividad_id):
        data = _cuerpo_json()    # El cuerpo es opcional: se puede finalizar sin observación.
        return jsonify(ejecucion_service.finalizar(actividad_id, usuario_actual(), data.get("observacion"))), 200

    @bp.post("/<actividad_id>/devolver")
    @requiere_rol(Rol.OPERARIO)
    def devolver_actividad(actividad_id):
        # Quien devuelve deja de ver la actividad: la respuesta es la constancia de la devolución.
        data = _cuerpo_json()
        return jsonify(ejecucion_service.devolver(
            actividad_id, usuario_actual(), data.get("motivo"), data.get("detalle"),
        )), 200

    # ---------- Evidencia de la ejecución: fotos y adjuntos ----------

    @bp.post("/<actividad_id>/evidencias")
    @requiere_rol(Rol.OPERARIO)
    def agregar_evidencia(actividad_id):
        # El archivo llega como multipart/form-data, en el campo "archivo".
        archivo = request.files.get("archivo")
        contenido = archivo.read() if archivo else b""
        nombre = archivo.filename if archivo else ""
        return jsonify(evidencia_service.agregar(actividad_id, usuario_actual(), contenido, nombre)), 201

    @bp.get("/<actividad_id>/evidencias/<evidencia_id>")
    @requiere_rol(Rol.OPERARIO, Rol.ADMINISTRADOR)
    def obtener_evidencia(actividad_id, evidencia_id):
        return _archivo(*evidencia_service.obtener(actividad_id, evidencia_id, usuario_actual()))

    # ---------- Adjuntos de la información de la actividad ----------

    @bp.post("/<actividad_id>/adjuntos")
    @requiere_rol(Rol.ADMINISTRADOR)
    def agregar_adjunto(actividad_id):
        archivo = request.files.get("archivo")
        contenido = archivo.read() if archivo else b""
        nombre = archivo.filename if archivo else ""
        return jsonify(adjunto_service.agregar(actividad_id, usuario_actual(), contenido, nombre)), 201

    @bp.get("/<actividad_id>/adjuntos/<adjunto_id>")
    @requiere_rol(Rol.OPERARIO, Rol.ADMINISTRADOR)
    def obtener_adjunto(actividad_id, adjunto_id):
        return _archivo(*adjunto_service.obtener(actividad_id, adjunto_id, usuario_actual()))

    return bp


def _archivo(contenido: bytes, tipo: str, nombre: str) -> Response:
    """Un archivo guardado (evidencia o adjunto), para verlo en el navegador."""
    respuesta = Response(contenido, mimetype=tipo)
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["Cache-Control"] = "private, max-age=3600"
    # "inline": el navegador lo muestra (foto o PDF) en lugar de descargarlo.
    respuesta.headers["Content-Disposition"] = f"inline; filename*=UTF-8''{quote(nombre)}"
    return respuesta


def _cuerpo_json() -> dict:
    """El cuerpo de la petición como diccionario; vacío si no viene o no es un objeto JSON."""
    data = request.get_json(force=True, silent=True)
    return data if isinstance(data, dict) else {}
