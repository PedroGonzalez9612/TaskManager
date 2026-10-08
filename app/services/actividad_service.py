from app.models.actividad import Actividad
from app.models.asignacion import Asignacion
from app.models.ejecucion import Ejecucion
from app.models.enums import Categoria, EstadoActividad, Prioridad, Rol
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError
from app.utils.fechas import validar_fecha, validar_hora

TIEMPO_ESTIMADO_MAXIMO_MIN = 24 * 60


class ActividadService:
    def __init__(self, actividad_repository, requerimiento_repository, asignacion_repository,
                 usuario_repository, ejecucion_repository, empresa_repository, carga_service):
        self.actividad_repository = actividad_repository
        self.requerimiento_repository = requerimiento_repository
        self.asignacion_repository = asignacion_repository
        self.usuario_repository = usuario_repository
        self.ejecucion_repository = ejecucion_repository
        self.empresa_repository = empresa_repository
        self.carga_service = carga_service

    # ---------- Crear, editar y eliminar (Administrador) ----------

    def crear_actividad(self, data: dict, solicitante: dict) -> dict:
        empresa_id = solicitante["empresa_id"]
        campos = self._validar_campos(data, empresa_id, parcial=False)
        operario_ids = self._validar_operarios(data.get("operario_ids") or [], empresa_id)

        consecutivo = self.empresa_repository.siguiente_consecutivo_actividad(empresa_id)
        actividad = Actividad(
            codigo=f"OT-{consecutivo:04d}",
            empresa_id=empresa_id,
            estado=EstadoActividad.ASIGNADA if operario_ids else EstadoActividad.PENDIENTE,
            **campos,
        )
        actividad_id = self.actividad_repository.insert(actividad.to_dict())
        self._reemplazar_asignaciones(actividad_id, operario_ids)
        return self._con_sobrecargas(self.obtener_actividad(actividad_id, solicitante))

    def actualizar_actividad(self, actividad_id: str, data: dict, solicitante: dict) -> dict:
        doc = self._buscar_de_la_empresa(actividad_id, solicitante["empresa_id"])
        campos = self._validar_campos(data, solicitante["empresa_id"], parcial=True)

        if "operario_ids" in data:
            operario_ids = self._validar_operarios(data.get("operario_ids") or [], solicitante["empresa_id"])
            self._reemplazar_asignaciones(actividad_id, operario_ids)
            # Solo cambia entre "sin asignar" y "por iniciar"; no toca una actividad ya iniciada o finalizada.
            if doc.get("estado") in (EstadoActividad.PENDIENTE.value, EstadoActividad.ASIGNADA.value):
                estado = EstadoActividad.ASIGNADA if operario_ids else EstadoActividad.PENDIENTE
                campos["estado"] = estado.value

        if campos:
            self.actividad_repository.update(actividad_id, campos)
        return self._con_sobrecargas(self.obtener_actividad(actividad_id, solicitante))

    def eliminar_actividad(self, actividad_id: str, solicitante: dict) -> None:
        self._buscar_de_la_empresa(actividad_id, solicitante["empresa_id"])
        self.asignacion_repository.delete_by_actividad(actividad_id)
        self.ejecucion_repository.delete_by_actividades([actividad_id])
        self.actividad_repository.delete(actividad_id)

    # ---------- Consultar (Administrador y Operario) ----------

    def obtener_actividad(self, actividad_id: str, solicitante: dict) -> dict:
        doc = self._buscar_de_la_empresa(actividad_id, solicitante["empresa_id"])
        if solicitante["rol"] == Rol.OPERARIO.value \
                and not self.asignacion_repository.existe(actividad_id, solicitante["id"]):
            raise ProhibidoError("Esta actividad no está asignada a ti")
        return self._presentar([doc])[0]

    def listar_actividades(self, filtros: dict, solicitante: dict) -> list:
        """El Administrador ve las actividades de su empresa; el Operario, solo las que tiene asignadas."""
        fecha_desde = validar_fecha(filtros["fecha_desde"], "La fecha inicial") if filtros.get("fecha_desde") else None
        fecha_hasta = validar_fecha(filtros["fecha_hasta"], "La fecha final") if filtros.get("fecha_hasta") else None

        ids = None
        if solicitante["rol"] == Rol.OPERARIO.value:
            ids = [a["actividad_id"] for a in self.asignacion_repository.find_by_usuario(solicitante["id"])]

        docs = self.actividad_repository.buscar(
            solicitante["empresa_id"],
            requerimiento_id=filtros.get("requerimiento_id"),
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            ids=ids,
        )
        return self._presentar(docs)

    # ---------- Validaciones ----------

    def _validar_campos(self, data: dict, empresa_id: str, parcial: bool) -> dict:
        """Valida los campos recibidos. Con parcial=True solo se revisan los que vengan en data."""
        campos = {}

        for campo in ("titulo", "ubicacion"):
            if campo in data or not parcial:
                valor = (data.get(campo) or "").strip()
                if not valor:
                    raise ValidationError(f"{campo} es obligatorio")
                campos[campo] = valor

        if "descripcion" in data or not parcial:
            campos["descripcion"] = (data.get("descripcion") or "").strip()

        if "requerimiento_id" in data or not parcial:
            requerimiento = self.requerimiento_repository.find_by_id(data.get("requerimiento_id"))
            if not requerimiento or requerimiento["empresa_id"] != empresa_id:
                raise NotFoundError("El requerimiento no existe en tu empresa")
            campos["requerimiento_id"] = data["requerimiento_id"]

        if "categoria" in data or not parcial:
            if data.get("categoria") not in [c.value for c in Categoria]:
                raise ValidationError("La categoría no es válida")
            campos["categoria"] = data["categoria"]

        if "prioridad" in data or not parcial:
            prioridad = data.get("prioridad", Prioridad.MEDIA.value)
            if prioridad not in [p.value for p in Prioridad]:
                raise ValidationError("La prioridad no es válida")
            campos["prioridad"] = prioridad

        if "tiempo_estimado_min" in data or not parcial:
            try:
                minutos = int(data.get("tiempo_estimado_min"))
            except (TypeError, ValueError):
                raise ValidationError("El tiempo estimado debe ser un número entero de minutos")
            if not 1 <= minutos <= TIEMPO_ESTIMADO_MAXIMO_MIN:
                raise ValidationError("El tiempo estimado debe estar entre 1 minuto y 24 horas")
            campos["tiempo_estimado_min"] = minutos

        if "fecha_programada" in data or not parcial:
            campos["fecha_programada"] = validar_fecha(data.get("fecha_programada"), "La fecha programada")

        if "hora_programada" in data:
            hora = data.get("hora_programada")
            campos["hora_programada"] = validar_hora(hora, "La hora programada") if hora else None

        return campos

    def _validar_operarios(self, operario_ids: list, empresa_id: str) -> list:
        if not isinstance(operario_ids, list):
            raise ValidationError("operario_ids debe ser una lista")
        operario_ids = list(dict.fromkeys(operario_ids))  # Quita repetidos conservando el orden.
        usuarios = self.usuario_repository.find_by_ids(operario_ids)
        validos = {
            str(u["_id"]) for u in usuarios
            if u.get("empresa_id") == empresa_id and u.get("rol") == Rol.OPERARIO.value
        }
        if len(validos) != len(operario_ids):
            raise ValidationError("Solo se puede asignar a operarios de tu empresa")
        return operario_ids

    def _buscar_de_la_empresa(self, actividad_id: str, empresa_id: str) -> dict:
        doc = self.actividad_repository.find_by_id(actividad_id)
        if not doc or doc.get("empresa_id") != empresa_id:
            raise NotFoundError("La actividad no existe")
        return doc

    # ---------- Apoyo ----------

    def _reemplazar_asignaciones(self, actividad_id: str, operario_ids: list) -> None:
        self.asignacion_repository.delete_by_actividad(actividad_id)
        for operario_id in operario_ids:
            asignacion = Asignacion(actividad_id=actividad_id, usuario_id=operario_id)
            self.asignacion_repository.insert(asignacion.to_dict())

    def _presentar(self, docs: list) -> list:
        """Convierte documentos en actividades listas para la interfaz, con sus operarios y su ejecución.
        Trae asignaciones, usuarios y ejecuciones en tres consultas, sin importar cuántas actividades sean."""
        ids = [str(doc["_id"]) for doc in docs]
        asignaciones = self.asignacion_repository.find_by_actividades(ids)
        usuarios = {
            str(u["_id"]): u["nombre"]
            for u in self.usuario_repository.find_by_ids(list({a["usuario_id"] for a in asignaciones}))
        }
        ejecuciones = {e["actividad_id"]: e for e in self.ejecucion_repository.find_by_actividades(ids)}

        operarios = {actividad_id: [] for actividad_id in ids}
        for asignacion in asignaciones:
            if asignacion["usuario_id"] in usuarios:
                operarios[asignacion["actividad_id"]].append(
                    {"id": asignacion["usuario_id"], "nombre": usuarios[asignacion["usuario_id"]]}
                )

        actividades = []
        for doc in docs:
            actividad = Actividad.from_doc(doc)
            actividad["operarios"] = sorted(operarios[actividad["id"]], key=lambda o: o["nombre"])
            ejecucion = ejecuciones.get(actividad["id"])
            actividad["ejecucion"] = Ejecucion.from_doc(ejecucion) if ejecucion else None
            actividades.append(actividad)
        return actividades

    def _con_sobrecargas(self, actividad: dict) -> dict:
        """Agrega el aviso de sobrecarga: operarios que con esta actividad superan el 100 % de su jornada."""
        actividad["sobrecargas"] = self.carga_service.sobrecargas(
            actividad["empresa_id"],
            actividad["fecha_programada"],
            [operario["id"] for operario in actividad["operarios"]],
        )
        return actividad
