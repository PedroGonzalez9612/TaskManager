from app.models.enums import EstadoRequerimiento
from app.models.requerimiento import Requerimiento
from app.utils.errors import NotFoundError, ValidationError


class RequerimientoService:
    """Requerimientos de una empresa. Todas las operaciones se limitan a la empresa del solicitante."""

    def __init__(self, requerimiento_repository, actividad_repository, asignacion_repository,
                 ejecucion_repository):
        self.requerimiento_repository = requerimiento_repository
        self.actividad_repository = actividad_repository
        self.asignacion_repository = asignacion_repository
        self.ejecucion_repository = ejecucion_repository

    def crear_requerimiento(self, data: dict, solicitante: dict) -> dict:
        titulo = (data.get("titulo") or "").strip()
        if not titulo:
            raise ValidationError("El título es obligatorio")

        requerimiento = Requerimiento(
            titulo=titulo,
            descripcion=(data.get("descripcion") or "").strip(),
            empresa_id=solicitante["empresa_id"],
        )
        requerimiento_id = self.requerimiento_repository.insert(requerimiento.to_dict())
        return self.obtener_requerimiento(requerimiento_id, solicitante)

    def obtener_requerimiento(self, requerimiento_id: str, solicitante: dict) -> dict:
        doc = self._buscar_de_la_empresa(requerimiento_id, solicitante["empresa_id"])
        requerimiento = Requerimiento.from_doc(doc)
        requerimiento["actividades"] = len(self.actividad_repository.find_by_requerimiento(requerimiento_id))
        return requerimiento

    def listar_requerimientos(self, solicitante: dict) -> list:
        docs = self.requerimiento_repository.find_by_empresa(solicitante["empresa_id"])
        cantidades = self.actividad_repository.contar_por_requerimiento(solicitante["empresa_id"])
        requerimientos = []
        for doc in docs:
            requerimiento = Requerimiento.from_doc(doc)
            requerimiento["actividades"] = cantidades.get(requerimiento["id"], 0)
            requerimientos.append(requerimiento)
        return requerimientos

    def actualizar_requerimiento(self, requerimiento_id: str, data: dict, solicitante: dict) -> dict:
        self._buscar_de_la_empresa(requerimiento_id, solicitante["empresa_id"])
        updates = {}
        if "titulo" in data:
            titulo = (data.get("titulo") or "").strip()
            if not titulo:
                raise ValidationError("El título no puede quedar vacío")
            updates["titulo"] = titulo
        if "descripcion" in data:
            updates["descripcion"] = (data.get("descripcion") or "").strip()
        if "estado" in data:
            if data["estado"] not in [e.value for e in EstadoRequerimiento]:
                raise ValidationError("El estado no es válido")
            updates["estado"] = data["estado"]
        if not updates:
            raise ValidationError("No hay campos válidos para actualizar")
        self.requerimiento_repository.update(requerimiento_id, updates)
        return self.obtener_requerimiento(requerimiento_id, solicitante)

    def eliminar_requerimiento(self, requerimiento_id: str, solicitante: dict) -> None:
        """Elimina el requerimiento junto con sus actividades, asignaciones y ejecuciones."""
        self._buscar_de_la_empresa(requerimiento_id, solicitante["empresa_id"])
        actividad_ids = [str(a["_id"]) for a in self.actividad_repository.find_by_requerimiento(requerimiento_id)]
        self.asignacion_repository.delete_by_actividades(actividad_ids)
        self.ejecucion_repository.delete_by_actividades(actividad_ids)
        self.actividad_repository.delete_by_requerimiento(requerimiento_id)
        self.requerimiento_repository.delete(requerimiento_id)

    def _buscar_de_la_empresa(self, requerimiento_id: str, empresa_id: str) -> dict:
        doc = self.requerimiento_repository.find_by_id(requerimiento_id)
        if not doc or doc.get("empresa_id") != empresa_id:
            raise NotFoundError("El requerimiento no existe")
        return doc
