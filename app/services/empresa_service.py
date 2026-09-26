from app.models.empresa import CAMPO_LIMITE_POR_ROL, Empresa
from app.models.enums import Rol
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError

TAMANO_MAXIMO_LOGO = 512 * 1024  # 512 KB
NOMBRE_ROL_PLURAL = {Rol.ADMINISTRADOR.value: "administradores", Rol.OPERARIO.value: "operarios"}


def detectar_tipo_imagen(contenido: bytes):
    """Reconoce la imagen por sus primeros bytes (no por la extensión, que se puede falsificar).
    No se aceptan SVG porque pueden contener código."""
    if contenido.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if contenido.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP":
        return "image/webp"
    return None


def leer_limite(valor, campo: str) -> int:
    try:
        limite = int(valor)
    except (TypeError, ValueError):
        raise ValidationError(f"{campo} debe ser un número entero")
    if limite < 1:
        raise ValidationError(f"{campo} debe ser al menos 1")
    return limite


class EmpresaService:
    def __init__(self, empresa_repository, usuario_repository):
        self.empresa_repository = empresa_repository
        self.usuario_repository = usuario_repository

    def crear_empresa(self, data: dict) -> dict:
        nombre = (data.get("nombre") or "").strip()
        nit = (data.get("nit") or "").strip()
        sector = (data.get("sector") or "").strip()
        direccion = (data.get("direccion") or "").strip()
        if not nombre or not nit or not sector or not direccion:
            raise ValidationError("nombre, nit, sector y direccion son obligatorios")

        limite_administradores = leer_limite(data.get("limite_administradores"), "El límite de administradores")
        limite_operarios = leer_limite(data.get("limite_operarios"), "El límite de operarios")

        if self.empresa_repository.find_by_nit(nit):
            raise ValidationError(f"Ya existe una empresa con el NIT {nit}")

        empresa = Empresa(
            nombre=nombre,
            nit=nit,
            sector=sector,
            direccion=direccion,
            limite_administradores=limite_administradores,
            limite_operarios=limite_operarios,
        )
        empresa_id = self.empresa_repository.insert(empresa.to_dict())
        return self.obtener_empresa(empresa_id)

    def obtener_empresa(self, empresa_id: str, solicitante: dict = None) -> dict:
        if solicitante:
            self.verificar_acceso(solicitante, empresa_id)
        doc = self.empresa_repository.find_by_id(empresa_id)
        if not doc:
            raise NotFoundError(f"Empresa {empresa_id} no encontrada")
        return self._con_usuarios_actuales(Empresa.from_doc(doc))

    def listar_empresas(self) -> list:
        docs = self.empresa_repository.find_all()
        return [self._con_usuarios_actuales(Empresa.from_doc(doc)) for doc in docs]

    def actualizar_empresa(self, empresa_id: str, data: dict) -> dict:
        empresa = self.obtener_empresa(empresa_id)
        updates = {}

        for campo in ("nombre", "sector", "direccion"):
            if campo in data:
                valor = (data.get(campo) or "").strip()
                if not valor:
                    raise ValidationError(f"{campo} no puede quedar vacío")
                updates[campo] = valor

        # Un límite no puede quedar por debajo de los usuarios que la empresa ya tiene.
        for rol, campo in CAMPO_LIMITE_POR_ROL.items():
            if campo in data:
                limite = leer_limite(data[campo], f"El límite de {NOMBRE_ROL_PLURAL[rol]}")
                actuales = empresa["usuarios_actuales"].get(rol, 0)
                if limite < actuales:
                    raise ValidationError(
                        f"La empresa ya tiene {actuales} {NOMBRE_ROL_PLURAL[rol]}; "
                        f"el límite no puede ser menor"
                    )
                updates[campo] = limite

        if not updates:
            raise ValidationError("No hay campos válidos para actualizar")
        self.empresa_repository.update(empresa_id, updates)
        return self.obtener_empresa(empresa_id)

    def guardar_logo(self, empresa_id: str, contenido: bytes) -> dict:
        self.obtener_empresa(empresa_id)
        if not contenido:
            raise ValidationError("Selecciona una imagen para el logo")
        if len(contenido) > TAMANO_MAXIMO_LOGO:
            raise ValidationError("El logo no puede pesar más de 512 KB")
        tipo = detectar_tipo_imagen(contenido)
        if not tipo:
            raise ValidationError("El logo debe ser una imagen PNG, JPG o WEBP")

        self.empresa_repository.update(empresa_id, {"logo": contenido, "logo_tipo": tipo})
        return self.obtener_empresa(empresa_id)

    def obtener_logo(self, empresa_id: str, solicitante: dict):
        """Devuelve (contenido, tipo) del logo."""
        self.verificar_acceso(solicitante, empresa_id)
        doc = self.empresa_repository.find_logo(empresa_id)
        if not doc or not doc.get("logo_tipo"):
            raise NotFoundError("La empresa no tiene logo")
        return bytes(doc["logo"]), doc["logo_tipo"]

    def eliminar_empresa(self, empresa_id: str) -> None:
        deleted = self.empresa_repository.delete(empresa_id)
        if not deleted:
            raise NotFoundError(f"Empresa {empresa_id} no encontrada")

    @staticmethod
    def verificar_acceso(solicitante: dict, empresa_id: str) -> None:
        """El Superadmin ve todas las empresas; los demás usuarios, solo la suya."""
        if solicitante["rol"] != Rol.SUPERADMIN.value and solicitante["empresa_id"] != empresa_id:
            raise ProhibidoError("No tienes acceso a esta empresa")

    def _con_usuarios_actuales(self, empresa: dict) -> dict:
        empresa["usuarios_actuales"] = self.usuario_repository.contar_por_rol(empresa["id"])
        return empresa
