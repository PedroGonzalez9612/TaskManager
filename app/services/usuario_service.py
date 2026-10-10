from app.models.empresa import CAMPO_LIMITE_POR_ROL
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.services.empresa_service import NOMBRE_ROL_PLURAL
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError

LONGITUD_MINIMA_CONTRASEÑA = 8


class UsuarioService:
    def __init__(self, usuario_repository, empresa_repository, turno_service=None):
        self.usuario_repository = usuario_repository
        self.empresa_repository = empresa_repository
        # Opcional: con él, la lista de usuarios trae el turno vigente hoy de cada operario.
        self.turno_service = turno_service

    def crear_usuario(self, data: dict, solicitante: dict) -> dict:
        nombre = (data.get("nombre") or "").strip()
        correo = (data.get("correo") or "").strip().lower()
        contraseña = data.get("contraseña") or ""
        rol = data.get("rol")

        if not nombre or not correo or not contraseña or not rol:
            raise ValidationError("nombre, correo, contraseña y rol son obligatorios")
        if len(contraseña) < LONGITUD_MINIMA_CONTRASEÑA:
            raise ValidationError(f"La contraseña debe tener al menos {LONGITUD_MINIMA_CONTRASEÑA} caracteres")

        empresa_id = self._empresa_destino(data, solicitante, rol)

        empresa = self.empresa_repository.find_by_id(empresa_id)
        if not empresa:
            raise NotFoundError(f"Empresa {empresa_id} no encontrada")
        self._verificar_limite(empresa, empresa_id, rol)
        if self.usuario_repository.find_by_correo(correo):
            raise ValidationError(f"Ya existe un usuario con el correo {correo}")

        usuario = Usuario(
            nombre=nombre,
            correo=correo,
            contraseña_hash=Usuario.hashear_contraseña(contraseña),
            rol=Rol(rol),
            empresa_id=empresa_id,
        )
        usuario_id = self.usuario_repository.insert(usuario.to_dict())
        return self.obtener_usuario(usuario_id, solicitante)

    def _empresa_destino(self, data: dict, solicitante: dict, rol: str) -> str:
        """Aplica quién puede crear a quién (Sección 4 del alcance) y decide la empresa del nuevo usuario."""
        if solicitante["rol"] == Rol.SUPERADMIN.value:
            if rol != Rol.ADMINISTRADOR.value:
                raise ProhibidoError("El Superadmin solo crea usuarios Administrador")
            if not data.get("empresa_id"):
                raise ValidationError("empresa_id es obligatorio")
            return data["empresa_id"]

        if solicitante["rol"] == Rol.ADMINISTRADOR.value:
            if rol not in (Rol.ADMINISTRADOR.value, Rol.OPERARIO.value):
                raise ValidationError("El rol debe ser ADMINISTRADOR u OPERARIO")
            # Un Administrador solo crea usuarios en su propia empresa, sin importar lo que envíe el cliente.
            return solicitante["empresa_id"]

        raise ProhibidoError("No tienes permiso para crear usuarios")

    def _verificar_limite(self, empresa: dict, empresa_id: str, rol: str) -> None:
        """Impide superar el límite de usuarios de ese rol que el Superadmin definió para la empresa."""
        limite = empresa.get(CAMPO_LIMITE_POR_ROL[rol])
        if limite is None:
            return
        actuales = self.usuario_repository.contar_por_rol(empresa_id).get(rol, 0)
        if actuales >= limite:
            raise ValidationError(
                f"La empresa alcanzó su límite de {limite} {NOMBRE_ROL_PLURAL[rol]}. "
                f"Solicita al Superadmin ampliar el límite."
            )

    def obtener_usuario(self, usuario_id: str, solicitante: dict) -> dict:
        doc = self.usuario_repository.find_by_id(usuario_id)
        if not doc:
            raise NotFoundError(f"Usuario {usuario_id} no encontrado")
        self._verificar_acceso_empresa(solicitante, doc.get("empresa_id"))
        return Usuario.from_doc(doc)

    def listar_usuarios(self, empresa_id: str, solicitante: dict) -> list:
        if solicitante["rol"] == Rol.ADMINISTRADOR.value:
            empresa_id = solicitante["empresa_id"]
        if not empresa_id:
            raise ValidationError("empresa_id es obligatorio")
        self._verificar_acceso_empresa(solicitante, empresa_id)
        usuarios = [Usuario.from_doc(doc) for doc in self.usuario_repository.find_by_empresa(empresa_id)]
        return self._con_turno_de_hoy(empresa_id, usuarios)

    def _con_turno_de_hoy(self, empresa_id: str, usuarios: list) -> list:
        """Agrega a cada operario su turno vigente hoy ("turno", o None si no tiene), leyendo los
        turnos de todos de una vez."""
        operario_ids = [u["id"] for u in usuarios if u["rol"] == Rol.OPERARIO.value]
        if self.turno_service is None or not operario_ids:
            return usuarios
        turnos = self.turno_service.turnos_de_hoy(empresa_id, operario_ids)
        return [{**u, "turno": turnos[u["id"]]} if u["id"] in turnos else u for u in usuarios]

    def actualizar_usuario(self, usuario_id: str, data: dict, solicitante: dict) -> dict:
        self.obtener_usuario(usuario_id, solicitante)
        nombre = (data.get("nombre") or "").strip()
        if not nombre:
            raise ValidationError("No hay campos válidos para actualizar")
        self.usuario_repository.update(usuario_id, {"nombre": nombre})
        return self.obtener_usuario(usuario_id, solicitante)

    def eliminar_usuario(self, usuario_id: str, solicitante: dict) -> None:
        if usuario_id == solicitante["id"]:
            raise ValidationError("No puedes eliminar tu propio usuario")
        self.obtener_usuario(usuario_id, solicitante)
        self.usuario_repository.delete(usuario_id)

    @staticmethod
    def _verificar_acceso_empresa(solicitante: dict, empresa_id: str) -> None:
        if solicitante["rol"] == Rol.SUPERADMIN.value:
            return
        if solicitante["rol"] == Rol.ADMINISTRADOR.value and solicitante["empresa_id"] == empresa_id:
            return
        raise ProhibidoError("No tienes acceso a los usuarios de esta empresa")
