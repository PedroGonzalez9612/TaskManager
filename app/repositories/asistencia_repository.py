from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError

from app.repositories.base_repository import BaseRepository

# Una asistencia está abierta mientras no tiene salida (en MongoDB, comparar con None incluye el
# campo ausente).
ABIERTA = {"salida": None}


class AsistenciaRepository(BaseRepository):
    """La asistencia de cada operario por jornada: marcas de entrada y salida, y la revisión del
    Administrador (alcance, Sección 5.1)."""

    def __init__(self, db):
        super().__init__(db["asistencias"])

    def crear_indices(self) -> None:
        # Una sola asistencia por operario y jornada. El servicio lo comprueba antes de insertar, pero
        # dos marcas de entrada simultáneas pasarían ambas; con este índice la base rechaza la segunda.
        self.collection.create_index(
            [("usuario_id", ASCENDING), ("jornada", ASCENDING)], unique=True, name="una_por_jornada")
        # Para la vista del Administrador: las asistencias de la empresa en una jornada.
        self.collection.create_index(
            [("empresa_id", ASCENDING), ("jornada", ASCENDING)], name="empresa_jornada")

    # ---------- Consultas ----------

    def find_de_usuario_en(self, usuario_id: str, jornada: str):
        return self.collection.find_one({"usuario_id": usuario_id, "jornada": jornada})

    def find_abierta_de_usuario(self, usuario_id: str):
        """La asistencia del operario con entrada y sin salida (la más reciente si hubiera varias)."""
        cursor = self.collection.find({"usuario_id": usuario_id, **ABIERTA}).sort("jornada", DESCENDING)
        return next(iter(cursor.limit(1)), None)

    def find_de_empresa_en(self, empresa_id: str, jornada: str):
        return list(self.collection.find({"empresa_id": empresa_id, "jornada": jornada}))

    # ---------- Escritura ----------

    def insertar(self, documento: dict):
        """Inserta la asistencia. Devuelve su id, o None si el operario ya tiene una en esa jornada."""
        try:
            return self.insert(documento)
        except DuplicateKeyError:
            return None

    def guardar(self, asistencia_id: str, documento: dict, estado_esperado: str,
                solo_si_abierta: bool = False) -> bool:
        """Guarda los campos de Asistencia.to_dict() solo si sigue en el estado esperado (y abierta,
        si se pide). Devuelve False si otra petición la cambió primero."""
        condicion = {"estado": estado_esperado, **(ABIERTA if solo_si_abierta else {})}
        return self.actualizar_si(asistencia_id, condicion, documento)
