from collections import defaultdict
from datetime import datetime, timezone

from app.models.proyecto import Proyecto
from app.utils.errors import NotFoundError, ValidationError


class ProyectoService:
    """Proyectos de una empresa: conjuntos de actividades (alcance, Sección 5.1). Solo los maneja el
    Administrador, y todas las operaciones se limitan a la empresa del solicitante.

    El avance no se guarda: se calcula cada vez con las horas estimadas de las actividades."""

    def __init__(self, proyecto_repository, actividad_repository, actividad_service, cierre_jornada,
                 reloj=None):
        self.proyecto_repository = proyecto_repository
        self.actividad_repository = actividad_repository
        self.actividad_service = actividad_service
        self.cierre_jornada = cierre_jornada
        self.reloj = reloj or (lambda: datetime.now(timezone.utc))

    def crear_proyecto(self, data: dict, solicitante: dict) -> dict:
        proyecto = Proyecto(    # La clase exige el nombre.
            nombre=self._texto(data.get("nombre")),
            descripcion=self._texto(data.get("descripcion")),
            empresa_id=solicitante["empresa_id"],
            creado_por_id=solicitante["id"],
            fecha_creacion=self.reloj(),
        )
        proyecto_id = self.proyecto_repository.insert(proyecto.to_dict())
        return self.obtener_proyecto(proyecto_id, solicitante)

    def listar_proyectos(self, solicitante: dict) -> list:
        """Los proyectos de la empresa, cada uno con su avance. Las actividades de todos se traen
        en una sola consulta."""
        self._cerrar_jornada(solicitante)
        empresa_id = solicitante["empresa_id"]
        proyectos = [Proyecto.from_doc(doc) for doc in self.proyecto_repository.find_by_empresa(empresa_id)]
        por_proyecto = self._actividades_por_proyecto(empresa_id, [proyecto["id"] for proyecto in proyectos])
        for proyecto in proyectos:
            proyecto["avance"] = Proyecto.calcular_avance(por_proyecto[proyecto["id"]])
        return proyectos

    def obtener_proyecto(self, proyecto_id: str, solicitante: dict) -> dict:
        """El proyecto con su avance y sus actividades, presentadas igual que en GET /actividades."""
        self._cerrar_jornada(solicitante)
        proyecto = Proyecto.from_doc(self._buscar_de_la_empresa(proyecto_id, solicitante["empresa_id"]))
        por_proyecto = self._actividades_por_proyecto(solicitante["empresa_id"], [proyecto_id])
        proyecto["avance"] = Proyecto.calcular_avance(por_proyecto[proyecto_id])
        proyecto["actividades"] = self.actividad_service.listar_actividades({"proyecto_id": proyecto_id}, solicitante)
        return proyecto

    def actualizar_proyecto(self, proyecto_id: str, data: dict, solicitante: dict) -> dict:
        doc = self._buscar_de_la_empresa(proyecto_id, solicitante["empresa_id"])
        if "nombre" not in data and "descripcion" not in data:
            raise ValidationError("No hay campos válidos para actualizar")
        # Se arma el proyecto con los datos nuevos para que la clase valide el nombre.
        proyecto = Proyecto(
            nombre=self._texto(data["nombre"]) if "nombre" in data else doc["nombre"],
            descripcion=self._texto(data["descripcion"]) if "descripcion" in data else doc.get("descripcion", ""),
            empresa_id=doc["empresa_id"],
        )
        self.proyecto_repository.update(proyecto_id, {"nombre": proyecto.nombre, "descripcion": proyecto.descripcion})
        return self.obtener_proyecto(proyecto_id, solicitante)

    def _cerrar_jornada(self, solicitante: dict) -> None:
        """Antes de calcular el avance: una actividad de hora fija que no se hizo ya cuenta como
        No realizada. Es el único punto de este servicio que llama al cierre."""
        self.cierre_jornada.cerrar_pendientes(solicitante["empresa_id"])

    def _actividades_por_proyecto(self, empresa_id: str, proyecto_ids: list) -> dict:
        por_proyecto = defaultdict(list)
        for actividad in self.actividad_repository.find_by_proyectos(empresa_id, proyecto_ids):
            por_proyecto[actividad["proyecto_id"]].append(actividad)
        return por_proyecto

    def _buscar_de_la_empresa(self, proyecto_id: str, empresa_id: str) -> dict:
        doc = self.proyecto_repository.find_by_id(proyecto_id)
        if not doc or doc.get("empresa_id") != empresa_id:
            raise NotFoundError("El proyecto no existe")
        return doc

    @staticmethod
    def _texto(valor) -> str:
        if valor is not None and not isinstance(valor, str):
            raise ValidationError("El nombre y la descripción deben ser texto")
        return valor or ""
