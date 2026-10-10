from app.utils.errors import ValidationError


class Proyecto:
    """Conjunto de actividades de una empresa. Solo el Administrador lo crea (alcance, Sección 5.1).

    No guarda su avance: se calcula con las horas estimadas de sus actividades."""

    def __init__(self, nombre, empresa_id, descripcion="", creado_por_id=None, fecha_creacion=None, id=None):
        nombre = (nombre or "").strip()
        if not nombre:
            raise ValidationError("El proyecto necesita un nombre")
        self.id = id
        self.nombre = nombre
        self.descripcion = (descripcion or "").strip()
        self.empresa_id = empresa_id
        self.creado_por_id = creado_por_id
        self.fecha_creacion = fecha_creacion

    @staticmethod
    def calcular_avance(actividades: list) -> dict:
        """Avance en horas: estimado de las finalizadas sobre el estimado total. Las canceladas salen
        del total; las no realizadas se quedan. Recibe diccionarios con "estado" y "tiempo_estimado_min"."""
        vigentes = [a for a in actividades if a.get("estado") != "CANCELADA"]
        total = sum(a.get("tiempo_estimado_min") or 0 for a in vigentes)
        hechas = sum(a.get("tiempo_estimado_min") or 0 for a in vigentes if a.get("estado") == "COMPLETADA")
        return {
            "minutos_finalizados": hechas,
            "minutos_totales": total,
            "porcentaje": round(hechas * 100 / total) if total else 0,
            "actividades": len(vigentes),
        }

    def to_dict(self) -> dict:
        return {
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "empresa_id": self.empresa_id,
            "creado_por_id": self.creado_por_id,
            "fecha_creacion": self.fecha_creacion,
        }

    @staticmethod
    def from_doc(doc) -> dict:
        return {
            "id": str(doc["_id"]),
            "nombre": doc["nombre"],
            "descripcion": doc.get("descripcion", ""),
            "empresa_id": doc.get("empresa_id"),
            "creado_por_id": doc.get("creado_por_id"),
            "fecha_creacion": doc.get("fecha_creacion"),
        }
