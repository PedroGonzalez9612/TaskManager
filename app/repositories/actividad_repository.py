from pymongo import ASCENDING

from app.models.enums import EstadoActividad
from app.repositories.base_repository import BaseRepository

ESTADOS_FINALES = [estado.value for estado in EstadoActividad if estado.es_final]
ORDEN_POR_FECHA = [("fecha_programada", ASCENDING), ("hora_programada", ASCENDING)]


class ActividadRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db["actividades"])

    def crear_indices(self) -> None:
        # Casi todas las consultas son "actividades de esta empresa en estas fechas".
        self.collection.create_index(
            [("empresa_id", ASCENDING), ("fecha_programada", ASCENDING)],
            name="empresa_fecha",
        )
        # Para "las actividades de este proyecto" y para el avance de varios proyectos a la vez.
        self.collection.create_index(
            [("empresa_id", ASCENDING), ("proyecto_id", ASCENDING)],
            name="empresa_proyecto",
        )

    def find_by_requerimiento(self, requerimiento_id: str):
        return list(self.collection.find({"requerimiento_id": requerimiento_id}))

    def buscar(self, empresa_id: str, requerimiento_id: str = None, fecha_desde: str = None,
               fecha_hasta: str = None, ids: list = None, estados: list = None,
               proyecto_id: str = None, independientes: bool = False):
        """Actividades de una empresa, con filtros opcionales. Las fechas son textos "AAAA-MM-DD"
        y los estados, valores de EstadoActividad.

        Con proyecto_id trae las de ese proyecto; con independientes=True, solo las que no pertenecen a
        ninguno. Si llegan los dos, manda proyecto_id."""
        filtro = {"empresa_id": empresa_id}
        if proyecto_id:
            filtro["proyecto_id"] = proyecto_id
        elif independientes:
            # En MongoDB, comparar con None incluye los documentos que no tienen el campo
            # (las actividades anteriores a los proyectos).
            filtro["proyecto_id"] = None
        if requerimiento_id:
            filtro["requerimiento_id"] = requerimiento_id
        if fecha_desde or fecha_hasta:
            rango = {}
            if fecha_desde:
                rango["$gte"] = fecha_desde
            if fecha_hasta:
                rango["$lte"] = fecha_hasta
            filtro["fecha_programada"] = rango
        if ids is not None:
            filtro["_id"] = {"$in": [oid for oid in map(self.to_object_id, ids) if oid]}
        if estados is not None:
            filtro["estado"] = {"$in": list(estados)}
        return list(self.collection.find(filtro).sort(ORDEN_POR_FECHA))

    def find_by_proyectos(self, empresa_id: str, proyecto_ids: list):
        """Las actividades de varios proyectos en una sola consulta, solo con lo que hace falta para
        calcular el avance: "proyecto_id", "estado" y "tiempo_estimado_min" (más "_id"). No sirve
        para mostrar la actividad: para eso está buscar(proyecto_id=...)."""
        if not proyecto_ids:
            return []
        filtro = {"empresa_id": empresa_id, "proyecto_id": {"$in": list(proyecto_ids)}}
        campos = {"proyecto_id": 1, "estado": 1, "tiempo_estimado_min": 1}
        return list(self.collection.find(filtro, campos))

    def guardar(self, actividad_id: str, documento: dict, estado_esperado: str = None) -> bool:
        """Guarda los campos de Actividad.to_dict(). Con estado_esperado, solo si la actividad sigue
        en ese estado: así, si alguien la inició mientras se cancelaba, el cambio no se aplica.
        Devuelve False si no se guardó (el estado ya era otro o el id no existe)."""
        condicion = {"estado": estado_esperado} if estado_esperado else {}
        return self.actualizar_si(actividad_id, condicion, documento)

    def buscar_abiertas_anteriores_a(self, empresa_id: str, fecha: str):
        """Actividades de la empresa programadas antes de esa fecha ("AAAA-MM-DD") que no llegaron
        a un estado final (COMPLETADA, NO_REALIZADA o CANCELADA). Qué hacer con ellas lo decide el servicio."""
        filtro = {
            "empresa_id": empresa_id,
            "fecha_programada": {"$lt": fecha},
            "estado": {"$nin": ESTADOS_FINALES},
        }
        return list(self.collection.find(filtro).sort(ORDEN_POR_FECHA))

    def contar_por_requerimiento(self, empresa_id: str) -> dict:
        grupos = self.collection.aggregate([
            {"$match": {"empresa_id": empresa_id}},
            {"$group": {"_id": "$requerimiento_id", "cantidad": {"$sum": 1}}},
        ])
        return {grupo["_id"]: grupo["cantidad"] for grupo in grupos}

    def delete_by_requerimiento(self, requerimiento_id: str) -> None:
        self.collection.delete_many({"requerimiento_id": requerimiento_id})

    def contar_por_estado(self, requerimiento_id: str = None):
        match_stage = {"$match": {"requerimiento_id": requerimiento_id}} if requerimiento_id else None
        pipeline = ([match_stage] if match_stage else []) + [
            {"$group": {"_id": "$estado", "total": {"$sum": 1}}},
        ]
        return list(self.collection.aggregate(pipeline))
