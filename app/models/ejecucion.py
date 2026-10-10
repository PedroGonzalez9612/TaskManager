from app.models.enums import EstadoEjecucion
from app.models.pausa import Pausa, minutos_entre
from app.utils.errors import ValidationError


class Ejecucion:
    """Registro del tiempo de UN operario en UNA actividad: pertenece a su asignación (decisión H1).

    Nace cuando el operario inicia. La pausa de un operario no pausa a sus compañeros, porque cada
    uno tiene su propia ejecución. La clase no lee el reloj: la hora de cada evento la pone el
    servidor y llega como parámetro ("ahora")."""

    def __init__(self, actividad_id, asignacion_id=None, usuario_id=None, fecha_inicio=None,
                 estado=EstadoEjecucion.EN_PROGRESO, fecha_fin=None, pausas=None, observacion=None, id=None):
        self.id = id
        self.asignacion_id = asignacion_id
        self.actividad_id = actividad_id    # Se repite aquí para consultar sin pasar por la asignación.
        self.usuario_id = usuario_id
        self.estado = EstadoEjecucion(estado)
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.pausas = list(pausas or [])
        self.observacion = observacion

    # ---------- Consultas ----------

    @property
    def esta_abierta(self) -> bool:
        return self.estado.esta_abierta

    def pausa_abierta(self):
        """La pausa que sigue sin terminar, o None. Solo puede haber una."""
        return next((pausa for pausa in self.pausas if pausa.esta_abierta), None)

    def tiempo_real_min(self, ahora) -> int:
        """Minutos trabajados: del inicio al fin (o hasta "ahora" si sigue abierta), sin las pausas."""
        hasta = self.fecha_fin or ahora
        total = minutos_entre(self.fecha_inicio, hasta)
        pausado = sum(pausa.duracion_min(hasta) for pausa in self.pausas)
        return max(0, round(total - pausado))

    # ---------- Transiciones ----------

    def pausar(self, motivo, ahora) -> Pausa:
        if self.estado != EstadoEjecucion.EN_PROGRESO:
            raise ValidationError("Solo se puede pausar una actividad que esté en curso")
        pausa = Pausa(motivo, inicio=ahora)
        self.pausas.append(pausa)
        self.estado = EstadoEjecucion.PAUSADA
        return pausa

    def reanudar(self, ahora) -> None:
        if self.estado != EstadoEjecucion.PAUSADA:
            raise ValidationError("Solo se puede reanudar una actividad que esté pausada")
        self.pausa_abierta().cerrar(ahora)
        self.estado = EstadoEjecucion.EN_PROGRESO

    def finalizar(self, ahora, observacion=None) -> None:
        if self.estado != EstadoEjecucion.EN_PROGRESO:
            raise ValidationError("Solo se puede finalizar una actividad que esté en curso")
        self.estado = EstadoEjecucion.FINALIZADA
        self.fecha_fin = ahora
        self.observacion = (observacion or "").strip() or None

    def cerrar(self, ahora) -> None:
        """Termina sin completarse (actividad cancelada o no realizada, u operario retirado).
        El tiempo trabajado hasta aquí se conserva."""
        if not self.esta_abierta:
            raise ValidationError("Esta ejecución ya terminó")
        pausa = self.pausa_abierta()
        if pausa:
            pausa.cerrar(ahora)
        self.estado = EstadoEjecucion.CERRADA
        self.fecha_fin = ahora

    # ---------- Persistencia y presentación ----------

    def to_dict(self) -> dict:
        return {
            "asignacion_id": self.asignacion_id,
            "actividad_id": self.actividad_id,
            "usuario_id": self.usuario_id,
            "estado": self.estado.value,
            "fecha_inicio": self.fecha_inicio,
            "fecha_fin": self.fecha_fin,
            "pausas": [pausa.to_dict() for pausa in self.pausas],
            "observacion": self.observacion,
        }

    @classmethod
    def desde_documento(cls, doc: dict) -> "Ejecucion":
        return cls(
            id=str(doc["_id"]),
            asignacion_id=doc.get("asignacion_id"),
            actividad_id=doc["actividad_id"],
            usuario_id=doc.get("usuario_id"),
            estado=doc.get("estado", EstadoEjecucion.EN_PROGRESO.value),
            fecha_inicio=doc.get("fecha_inicio"),
            fecha_fin=doc.get("fecha_fin"),
            pausas=[Pausa.desde_documento(pausa) for pausa in doc.get("pausas", [])],
            observacion=doc.get("observacion"),
        )

    def presentar(self, ahora) -> dict:
        """La ejecución lista para la API, con el tiempo real ya calculado."""
        datos = self.to_dict()
        datos["id"] = self.id
        datos["tiempo_real_min"] = self.tiempo_real_min(ahora)
        return datos

    @staticmethod
    def from_doc(doc):
        """Forma anterior (diccionario sin cálculos). La usan los servicios que aún no se han actualizado."""
        return {
            "id": str(doc["_id"]),
            "actividad_id": doc["actividad_id"],
            "estado": doc.get("estado", EstadoEjecucion.EN_PROGRESO.value),
            "fecha_inicio": doc.get("fecha_inicio"),
            "fecha_fin": doc.get("fecha_fin"),
        }
