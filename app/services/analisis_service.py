from app.utils.errors import NotFoundError


class AnalisisService:
    def __init__(self, actividad_repository, requerimiento_repository, registro_tiempo_repository):
        self.actividad_repository = actividad_repository
        self.requerimiento_repository = requerimiento_repository
        self.registro_tiempo_repository = registro_tiempo_repository

    def horas_por_actividad(self) -> list:
        result = self.registro_tiempo_repository.total_horas_por_actividad()
        return [{"actividad_id": r["_id"], "total_horas": r["total_horas"]} for r in result]

    def horas_por_usuario(self) -> list:
        result = self.registro_tiempo_repository.total_horas_por_usuario()
        return [{"usuario_id": r["_id"], "total_horas": r["total_horas"]} for r in result]

    def actividades_por_estado(self, requerimiento_id: str = None) -> list:
        result = self.actividad_repository.contar_por_estado(requerimiento_id)
        return [{"estado": r["_id"], "total": r["total"]} for r in result]

    def resumen_requerimiento(self, requerimiento_id: str) -> dict:
        requerimiento_doc = self.requerimiento_repository.find_by_id(requerimiento_id)
        if not requerimiento_doc:
            raise NotFoundError(f"Requerimiento {requerimiento_id} no encontrado")

        actividades = self.actividad_repository.find_by_requerimiento(requerimiento_id)
        actividad_ids = [str(a["_id"]) for a in actividades]
        total_horas = self.registro_tiempo_repository.total_horas_por_actividades(actividad_ids)

        por_estado = {}
        for actividad in actividades:
            estado = actividad.get("estado")
            por_estado[estado] = por_estado.get(estado, 0) + 1

        return {
            "requerimiento_id": requerimiento_id,
            "titulo": requerimiento_doc.get("titulo"),
            "total_actividades": len(actividades),
            "actividades_por_estado": por_estado,
            "total_horas_invertidas": total_horas,
        }
