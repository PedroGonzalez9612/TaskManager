from app.models.enums import Prioridad

SIN_HORA_AL_FINAL = "99:99"


def orden_sugerido(actividades: list) -> list:
    """El orden que propone el sistema: primero la mayor prioridad (por su peso, nunca comparando
    textos), después la hora, y entre iguales la que lleva más días de retraso."""
    return sorted(actividades, key=lambda actividad: (
        -Prioridad(actividad["prioridad"]).peso,
        actividad.get("hora_programada") or SIN_HORA_AL_FINAL,
        -(actividad.get("dias_de_retraso") or 0),
    ))


class OrdenJornada:
    """El orden que un operario eligió para sus actividades de horario flexible en una jornada
    (alcance, Sección 5.1). Si no eligió ninguno, vale el sugerido."""

    def __init__(self, usuario_id, fecha, actividad_ids=None, fecha_actualizacion=None, id=None):
        self.id = id
        self.usuario_id = usuario_id
        self.fecha = fecha                              # "AAAA-MM-DD": la jornada.
        self.actividad_ids = list(dict.fromkeys(actividad_ids or []))    # Sin repetidos, en su orden.
        self.fecha_actualizacion = fecha_actualizacion

    @property
    def es_personalizado(self) -> bool:
        return bool(self.actividad_ids)

    def aplicar(self, actividades: list) -> list:
        """Ordena las actividades: primero las que el operario acomodó, en su orden; después las
        demás (por ejemplo, las que le asignaron más tarde), en el orden sugerido. Los ids que ya
        no correspondan a ninguna actividad se ignoran."""
        posicion = {actividad_id: indice for indice, actividad_id in enumerate(self.actividad_ids)}
        elegidas = sorted((a for a in actividades if a["id"] in posicion), key=lambda a: posicion[a["id"]])
        return elegidas + orden_sugerido([a for a in actividades if a["id"] not in posicion])

    def to_dict(self) -> dict:
        return {
            "usuario_id": self.usuario_id,
            "fecha": self.fecha,
            "actividad_ids": self.actividad_ids,
            "fecha_actualizacion": self.fecha_actualizacion,
        }

    @classmethod
    def desde_documento(cls, doc: dict) -> "OrdenJornada":
        return cls(
            id=str(doc["_id"]),
            usuario_id=doc["usuario_id"],
            fecha=doc["fecha"],
            actividad_ids=doc.get("actividad_ids", []),
            fecha_actualizacion=doc.get("fecha_actualizacion"),
        )
