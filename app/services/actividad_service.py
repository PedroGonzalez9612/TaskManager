from datetime import date, datetime, timezone

from app.models.actividad import Actividad
from app.models.asignacion import Asignacion
from app.models.ejecucion import Ejecucion
from app.models.enums import Categoria, EstadoActividad, EstadoAsignacion, EstadoEjecucion, Prioridad, Rol
from app.services.catalogo_service import MOTIVO_CANCELACION, resolver_motivo
from app.services.estado_actividad import calcular_estado_actividad, estado_para_operario
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError
from app.utils.fechas import validar_fecha, validar_hora
from app.utils.reloj import fecha_local

TIEMPO_ESTIMADO_MAXIMO_MIN = 24 * 60
# Si otra petición cambia el estado de la actividad mientras se recalcula, se vuelve a calcular.
INTENTOS_RECALCULAR_ESTADO = 3

# Estados en los que una actividad no tiene quién la haga: el Administrador debe atenderlas.
ESTADOS_SIN_OPERARIO = (EstadoActividad.PENDIENTE.value, EstadoActividad.DEVUELTA.value)

# Campos de una actividad que solo se revisan cuando vienen en la petición.
CAMPOS_OPCIONALES = ("proyecto_id", "requerimiento_id", "hora_programada")


def _texto_obligatorio(valor, campo: str) -> str:
    texto = (valor or "").strip()
    if not texto:
        raise ValidationError(f"{campo} es obligatorio")
    return texto


def _validar_categoria(valor) -> str:
    if valor not in [categoria.value for categoria in Categoria]:
        raise ValidationError("La categoría no es válida")
    return valor


def _validar_prioridad(valor) -> str:
    """Sin prioridad indicada, la actividad queda en Media."""
    prioridad = Prioridad.MEDIA.value if valor is None else valor
    if prioridad not in [p.value for p in Prioridad]:
        raise ValidationError("La prioridad no es válida")
    return prioridad


def _dias_de_retraso(actividad: dict) -> int:
    """Días que lleva de retraso una actividad reprogramada: de su fecha original a la programada."""
    if not actividad["reprogramada"]:
        return 0
    original = date.fromisoformat(actividad["fecha_original"])
    programada = date.fromisoformat(actividad["fecha_programada"])
    return max(0, (programada - original).days)


def _validar_tiempo_estimado(valor) -> int:
    try:
        minutos = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("El tiempo estimado debe ser un número entero de minutos")
    if not 1 <= minutos <= TIEMPO_ESTIMADO_MAXIMO_MIN:
        raise ValidationError("El tiempo estimado debe estar entre 1 minuto y 24 horas")
    return minutos


class ActividadService:
    def __init__(self, actividad_repository, requerimiento_repository, asignacion_repository,
                 usuario_repository, ejecucion_repository, empresa_repository, carga_service,
                 proyecto_repository, catalogo_service, cierre_jornada, reloj=None):
        # La hora de todo evento la pone el servidor. Las pruebas pasan un reloj que ellas controlan.
        self.reloj = reloj or (lambda: datetime.now(timezone.utc))
        self.actividad_repository = actividad_repository
        self.requerimiento_repository = requerimiento_repository
        self.asignacion_repository = asignacion_repository
        self.usuario_repository = usuario_repository
        self.ejecucion_repository = ejecucion_repository
        self.empresa_repository = empresa_repository
        self.carga_service = carga_service
        self.proyecto_repository = proyecto_repository
        self.catalogo_service = catalogo_service
        self.cierre_jornada = cierre_jornada

    # ---------- Crear, editar, cancelar y eliminar (Administrador) ----------

    def crear_actividad(self, data: dict, solicitante: dict) -> dict:
        self._cerrar_jornada(solicitante)
        empresa_id = solicitante["empresa_id"]
        campos = self._validar_campos(data, empresa_id, parcial=False)
        self._exigir_fecha_vigente(campos["fecha_programada"], empresa_id)
        operario_ids = self._validar_operarios(data.get("operario_ids") or [], empresa_id)

        consecutivo = self.empresa_repository.siguiente_consecutivo_actividad(empresa_id)
        # La clase deja la fecha original igual a la fecha programada.
        actividad = Actividad(
            codigo=f"OT-{consecutivo:04d}",
            empresa_id=empresa_id,
            estado=EstadoActividad.ASIGNADA if operario_ids else EstadoActividad.PENDIENTE,
            **campos,
        )
        actividad_id = self.actividad_repository.insert(actividad.to_dict())
        self._sincronizar_asignaciones(actividad_id, operario_ids, solicitante, self.reloj())
        return self._con_sobrecargas(self._consultar(actividad_id, solicitante))

    def actualizar_actividad(self, actividad_id: str, data: dict, solicitante: dict) -> dict:
        self._cerrar_jornada(solicitante)
        doc = self._buscar_de_la_empresa(actividad_id, solicitante["empresa_id"])
        if self._estado_de(doc).es_final:
            raise ValidationError(
                "Esta actividad ya está cerrada (finalizada, no realizada o cancelada): "
                "no se puede editar ni reasignar"
            )
        campos = self._validar_campos(data, solicitante["empresa_id"], parcial=True)
        if campos.get("fecha_programada", doc.get("fecha_programada")) != doc.get("fecha_programada"):
            self._exigir_fecha_vigente(campos["fecha_programada"], solicitante["empresa_id"])
        # Se valida todo antes de guardar, para no dejar la actividad a medio cambiar.
        operario_ids = None
        if "operario_ids" in data:
            operario_ids = self._validar_operarios(data.get("operario_ids") or [], solicitante["empresa_id"])

        if campos:
            self.actividad_repository.update(actividad_id, campos)
        if operario_ids is not None:
            self._sincronizar_asignaciones(actividad_id, operario_ids, solicitante, self.reloj())
        return self._con_sobrecargas(self._consultar(actividad_id, solicitante))

    def cancelar(self, actividad_id: str, solicitante: dict, motivo, detalle=None) -> dict:
        """El Administrador cancela una actividad sin iniciar o pausada (alcance, Sección 5.1). No se
        borra: queda con su motivo, quién la canceló y cuándo."""
        self._cerrar_jornada(solicitante)
        ahora = self.reloj()
        doc = self._buscar_de_la_empresa(actividad_id, solicitante["empresa_id"])
        elegido = resolver_motivo(motivo, detalle)
        actividad = Actividad.desde_documento(doc)
        estado_leido = actividad.estado.value

        actividad.cancelar(elegido.texto, solicitante["id"], ahora)    # Valida el estado y el motivo.
        # Solo se guarda si el estado sigue siendo el que se leyó: si un operario la inició mientras
        # tanto, la cancelación no se aplica.
        if not self.actividad_repository.guardar(actividad_id, actividad.to_dict(), estado_esperado=estado_leido):
            raise ValidationError("La actividad cambió mientras la cancelabas; revisa su estado")

        self._cerrar_ejecuciones_abiertas(actividad_id, ahora)
        self.catalogo_service.registrar_motivo(solicitante["empresa_id"], MOTIVO_CANCELACION, elegido)
        return self._consultar(actividad_id, solicitante)

    def eliminar_actividad(self, actividad_id: str, solicitante: dict) -> None:
        # Se retira con los requerimientos: cancelar reemplaza al borrado (alcance, Sección 5.1).
        self._buscar_de_la_empresa(actividad_id, solicitante["empresa_id"])
        self.asignacion_repository.delete_by_actividad(actividad_id)
        self.ejecucion_repository.delete_by_actividades([actividad_id])
        self.actividad_repository.delete(actividad_id)

    # ---------- Consultar (Administrador y Operario) ----------

    def obtener_actividad(self, actividad_id: str, solicitante: dict) -> dict:
        self._cerrar_jornada(solicitante)
        return self._consultar(actividad_id, solicitante)

    def _consultar(self, actividad_id: str, solicitante: dict) -> dict:
        """La actividad ya presentada. Lo usan las operaciones que ya cerraron la jornada."""
        doc = self._buscar_de_la_empresa(actividad_id, solicitante["empresa_id"])
        if solicitante["rol"] == Rol.OPERARIO.value \
                and not self.asignacion_repository.existe(actividad_id, solicitante["id"]):
            raise ProhibidoError("Esta actividad no está asignada a ti")
        return self._presentar([doc], solicitante)[0]

    def listar_actividades(self, filtros: dict, solicitante: dict) -> list:
        """El Administrador ve las actividades de su empresa; el Operario, solo las que tiene asignadas.
        Con "proyecto_id" trae las de ese proyecto; con "independientes", las que no pertenecen a ninguno;
        con "sin_asignar", las que no tienen operario (nunca asignadas o devueltas)."""
        self._cerrar_jornada(solicitante)
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
            proyecto_id=filtros.get("proyecto_id"),
            independientes=bool(filtros.get("independientes")),
            estados=ESTADOS_SIN_OPERARIO if filtros.get("sin_asignar") else None,
        )
        return self._presentar(docs, solicitante)

    def _cerrar_jornada(self, solicitante: dict) -> None:
        """Antes de leer o cambiar actividades: lo que quedó abierto en días anteriores se reprograma
        o queda como No realizado (alcance, Sección 5.1). Es el único punto de este servicio que
        llama al cierre."""
        self.cierre_jornada.cerrar_pendientes(solicitante["empresa_id"])

    # ---------- Validaciones ----------

    def _exigir_fecha_vigente(self, fecha: str, empresa_id: str) -> None:
        """Una actividad no se programa ni se mueve a un día que ya pasó (alcance, Sección 5.1).
        "Hoy" es el día de la empresa, según su zona horaria."""
        empresa = self.empresa_repository.find_by_id(empresa_id) or {}
        if fecha < fecha_local(self.reloj(), empresa.get("zona_horaria")):
            raise ValidationError("La fecha programada no puede ser anterior a hoy")

    def _validar_campos(self, data: dict, empresa_id: str, parcial: bool) -> dict:
        """Valida los campos recibidos. Con parcial=True solo se revisan los que vengan en data.
        Los opcionales (proyecto, requerimiento y hora) solo se revisan cuando vienen."""
        validadores = {
            "titulo": lambda valor: _texto_obligatorio(valor, "titulo"),
            "ubicacion": lambda valor: _texto_obligatorio(valor, "ubicacion"),
            "descripcion": lambda valor: (valor or "").strip(),
            # Una actividad sin proyecto es una actividad independiente. El requerimiento es el dato anterior
            # a los proyectos: sigue aceptándose, ya no es obligatorio, y se retira con ellos.
            "proyecto_id": lambda valor: self._validar_proyecto(valor, empresa_id),
            "requerimiento_id": lambda valor: self._validar_requerimiento(valor, empresa_id),
            "categoria": _validar_categoria,
            "prioridad": _validar_prioridad,
            "tiempo_estimado_min": _validar_tiempo_estimado,
            "fecha_programada": lambda valor: validar_fecha(valor, "La fecha programada"),
            "hora_programada": lambda valor: validar_hora(valor, "La hora programada") if valor else None,
        }
        campos = {}
        for campo, validar in validadores.items():
            exigido = not parcial and campo not in CAMPOS_OPCIONALES
            if campo in data or exigido:
                campos[campo] = validar(data.get(campo))
        return campos

    def _validar_proyecto(self, proyecto_id, empresa_id: str):
        """El id del proyecto si es de la empresa; None si viene vacío (la actividad queda independiente)."""
        if not proyecto_id:
            return None
        proyecto = self.proyecto_repository.find_by_id(proyecto_id)
        if not proyecto or proyecto.get("empresa_id") != empresa_id:
            raise ValidationError("El proyecto no existe en tu empresa")
        return str(proyecto["_id"])

    def _validar_requerimiento(self, requerimiento_id, empresa_id: str):
        if not requerimiento_id:
            return None
        requerimiento = self.requerimiento_repository.find_by_id(requerimiento_id)
        if not requerimiento or requerimiento["empresa_id"] != empresa_id:
            raise NotFoundError("El requerimiento no existe en tu empresa")
        return str(requerimiento["_id"])

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

    @staticmethod
    def _estado_de(doc: dict) -> EstadoActividad:
        return EstadoActividad(doc.get("estado", EstadoActividad.PENDIENTE.value))

    # ---------- Asignaciones y estado ----------

    def _sincronizar_asignaciones(self, actividad_id: str, operario_ids: list, solicitante: dict, ahora) -> None:
        """Deja la actividad asignada a "operario_ids" sin borrar nada (alcance, Sección 5.1): al que
        sale se le retira la asignación, al que entra se le crea una nueva y al que sigue no se le
        toca (conserva su fecha de asignación y su ejecución). Después recalcula el estado."""
        activas = [
            Asignacion.desde_documento(doc)
            for doc in self.asignacion_repository.find_by_actividad(actividad_id)
        ]
        ya_asignados = {asignacion.usuario_id for asignacion in activas}

        for asignacion in activas:
            if asignacion.usuario_id not in operario_ids:
                self._retirar_asignacion(asignacion, solicitante["id"], ahora)

        for operario_id in operario_ids:
            if operario_id not in ya_asignados:
                nueva = Asignacion(actividad_id=actividad_id, usuario_id=operario_id,
                                   fecha_asignacion=ahora, asignada_por_id=solicitante["id"])
                # Devuelve None si otro administrador lo asignó al mismo tiempo: ya quedó asignado.
                self.asignacion_repository.insertar_activa(nueva.to_dict())

        self.recalcular_estado(actividad_id)

    def _retirar_asignacion(self, asignacion: Asignacion, autor_id: str, ahora) -> None:
        """El Administrador le quita la actividad a un operario. Si la tenía en curso o pausada, su
        ejecución se cierra y conserva el tiempo trabajado."""
        asignacion.retirar(autor_id, ahora)
        retirada = self.asignacion_repository.actualizar_si(
            asignacion.id, {"estado": EstadoAsignacion.ACTIVA.value}, asignacion.to_dict(),
        )
        if not retirada:
            return  # Otra petición ya la había cerrado.

        doc = self.ejecucion_repository.find_by_asignacion(asignacion.id)
        if doc:
            self._cerrar_si_esta_abierta(Ejecucion.desde_documento(doc), ahora)

    def _cerrar_ejecuciones_abiertas(self, actividad_id: str, ahora) -> None:
        """Al cancelar: las ejecuciones que quedaron pausadas se cierran y conservan su tiempo."""
        for doc in self.ejecucion_repository.find_abiertas_de_actividad(actividad_id):
            self._cerrar_si_esta_abierta(Ejecucion.desde_documento(doc), ahora)

    def _cerrar_si_esta_abierta(self, ejecucion: Ejecucion, ahora) -> None:
        if ejecucion.esta_abierta:
            estado_anterior = ejecucion.estado.value
            ejecucion.cerrar(ahora)
            self.ejecucion_repository.guardar(ejecucion.id, ejecucion.to_dict(), estado_esperado=estado_anterior)

    def recalcular_estado(self, actividad_id: str, por_devolucion: bool = False) -> None:
        """Calcula el estado de la actividad a partir de sus asignaciones activas y de la ejecución
        de cada una, y lo guarda si cambió. La regla está en estado_actividad.py. Lo llaman este
        servicio (al asignar) y EjecucionService (después de iniciar, pausar, reanudar, finalizar o
        devolver; en ese último caso con por_devolucion=True)."""
        for _ in range(INTENTOS_RECALCULAR_ESTADO):
            doc = self.actividad_repository.find_by_id(actividad_id)
            if not doc:
                return
            actual = self._estado_de(doc)
            asignaciones = self.asignacion_repository.find_by_actividad(actividad_id)
            estado_por_asignacion = {
                ejecucion.get("asignacion_id"): ejecucion.get("estado")
                for ejecucion in self.ejecucion_repository.find_by_actividades([actividad_id])
            }
            nuevo = calcular_estado_actividad(
                actual, [estado_por_asignacion.get(str(asignacion["_id"])) for asignacion in asignaciones],
                por_devolucion=por_devolucion,
            )
            if nuevo == actual:
                return
            # Solo se guarda si el estado sigue siendo el que se leyó: si dos operarios terminan al
            # tiempo, el segundo vuelve a calcular con los datos ya actualizados.
            if self.actividad_repository.actualizar_si(
                    actividad_id, {"estado": actual.value}, {"estado": nuevo.value}):
                return

    # ---------- Presentación ----------

    def _presentar(self, docs: list, solicitante: dict) -> list:
        """Convierte documentos en actividades listas para la interfaz, con sus operarios y la
        ejecución de cada uno. Trae asignaciones, usuarios y ejecuciones en tres consultas, sin
        importar cuántas actividades sean.

        "estado_general" es el estado de la actividad. "estado" y "ejecucion" dependen de quién
        pregunta: el Operario ve los suyos; el Administrador, los generales."""
        ahora = self.reloj()
        ids = [str(doc["_id"]) for doc in docs]
        # Con el historial: las asignaciones devueltas dicen quién devolvió la actividad y por qué.
        asignaciones = self.asignacion_repository.find_by_actividades(ids, incluir_historial=True)
        usuario_ids = {a["usuario_id"] for a in asignaciones}
        usuario_ids.update(doc["cancelacion"].get("autor_id") for doc in docs if doc.get("cancelacion"))
        nombres = {
            str(u["_id"]): u["nombre"]
            for u in self.usuario_repository.find_by_ids([usuario_id for usuario_id in usuario_ids if usuario_id])
        }
        ejecuciones = {
            doc["asignacion_id"]: Ejecucion.desde_documento(doc)
            for doc in self.ejecucion_repository.find_by_actividades(ids) if doc.get("asignacion_id")
        }

        # Por actividad: (id del operario, nombre, su ejecución o None), solo de asignaciones activas.
        equipos = {actividad_id: [] for actividad_id in ids}
        devoluciones = {actividad_id: [] for actividad_id in ids}
        for doc in asignaciones:
            asignacion = Asignacion.desde_documento(doc)
            if asignacion.esta_activa and asignacion.usuario_id in nombres:
                equipos[asignacion.actividad_id].append(
                    (asignacion.usuario_id, nombres[asignacion.usuario_id], ejecuciones.get(asignacion.id))
                )
            elif asignacion.devolucion:
                devoluciones[asignacion.actividad_id].append({
                    "operario_id": asignacion.usuario_id,
                    "operario_nombre": nombres.get(asignacion.usuario_id),
                    **asignacion.devolucion.to_dict(),
                })

        es_operario = solicitante["rol"] == Rol.OPERARIO.value
        actividades = []
        for doc in docs:
            actividad = Actividad.from_doc(doc)
            actividad["dias_de_retraso"] = _dias_de_retraso(actividad)
            equipo = sorted(equipos[actividad["id"]], key=lambda fila: fila[1])
            self._agregar_ejecucion(actividad, equipo, solicitante, ahora)
            # Quién devolvió la actividad y por qué es información para el Administrador.
            actividad["devoluciones"] = [] if es_operario else sorted(
                devoluciones[actividad["id"]], key=lambda devolucion: devolucion["fecha"],
            )
            if actividad["cancelacion"]:
                actividad["cancelacion"] = {
                    **actividad["cancelacion"],
                    "autor_nombre": nombres.get(actividad["cancelacion"].get("autor_id")),
                }
            actividades.append(actividad)
        return actividades

    @staticmethod
    def _agregar_ejecucion(actividad: dict, equipo: list, solicitante: dict, ahora) -> None:
        """Agrega a la actividad lo que lleva cada operario y el resumen ("1 de 2 finalizaron")."""
        presentadas = []    # (id del operario, ejecución lista para la API), de los que ya iniciaron.
        for usuario_id, nombre, ejecucion in equipo:
            if ejecucion:
                presentadas.append((usuario_id, {**ejecucion.presentar(ahora), "operario_nombre": nombre}))

        actividad["operarios"] = [
            {"id": usuario_id, "nombre": nombre, "estado_ejecucion": ejecucion.estado.value if ejecucion else None}
            for usuario_id, nombre, ejecucion in equipo
        ]
        actividad["ejecuciones"] = [presentada for _, presentada in presentadas]
        actividad["total_asignados"] = len(equipo)
        actividad["finalizados"] = sum(
            1 for _, presentada in presentadas if presentada["estado"] == EstadoEjecucion.FINALIZADA.value
        )
        actividad["tiempo_real_min"] = sum(presentada["tiempo_real_min"] for _, presentada in presentadas)
        actividad["estado_general"] = actividad["estado"]

        if solicitante["rol"] == Rol.OPERARIO.value:
            propia = next((p for usuario_id, p in presentadas if usuario_id == solicitante["id"]), None)
            actividad["ejecucion"] = propia
            actividad["estado"] = estado_para_operario(
                actividad["estado_general"], propia["estado"] if propia else None,
            ).value
        else:
            abiertas = [p for _, p in presentadas if EstadoEjecucion(p["estado"]).esta_abierta]
            actividad["ejecucion"] = next(iter(abiertas or [p for _, p in presentadas]), None)

    def _con_sobrecargas(self, actividad: dict) -> dict:
        """Agrega el aviso de sobrecarga: operarios que con esta actividad superan el 100 % de su jornada."""
        actividad["sobrecargas"] = self.carga_service.sobrecargas(
            actividad["empresa_id"],
            actividad["fecha_programada"],
            [operario["id"] for operario in actividad["operarios"]],
        )
        return actividad
