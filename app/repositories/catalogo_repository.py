import unicodedata

from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from app.repositories.base_repository import BaseRepository


def limpiar_valor(valor: str) -> str:
    """El texto como se guarda y se muestra: sin espacios al inicio ni al final, y con un solo
    espacio entre palabras. Conserva las mayúsculas y las tildes que escribió la persona."""
    return " ".join((valor or "").split())


def clave_de(valor: str) -> str:
    """La clave que evita valores repetidos: el valor limpio (ver limpiar_valor) y en minúsculas.

    "Falta  Repuesto " y "falta repuesto" tienen la misma clave y cuentan como el mismo valor.
    Las tildes sí distinguen: "Daño electrico" y "Daño eléctrico" son dos valores."""
    return limpiar_valor(valor).lower()


def _orden_alfabetico(valor: str) -> tuple:
    """Para ordenar como en un diccionario en español: sin distinguir mayúsculas ni tildes
    (si no, "Árbol" quedaría después de "Zona")."""
    sin_tildes = "".join(
        letra for letra in unicodedata.normalize("NFD", valor.lower())
        if unicodedata.category(letra) != "Mn"
    )
    return (sin_tildes, valor)


class CatalogoRepository(BaseRepository):
    """Listas desplegables por empresa que se van llenando con lo que se escribe en "Otro"
    (alcance, Sección 5.1). El tipo es un valor de TipoCatalogo.

    Un documento por valor: {empresa_id, tipo, valor, clave}. "valor" es el texto que se muestra y
    "clave" su forma normalizada (ver clave_de). Aquí solo está lo que las personas escribieron:
    los motivos fijos del sistema los agrega quien arma la lista, no este repositorio."""

    def __init__(self, db):
        super().__init__(db["catalogos"])

    def crear_indices(self) -> None:
        # Impide el mismo valor dos veces en un catálogo, aunque lleguen dos peticiones a la vez.
        # También sirve para listar: empieza por (empresa_id, tipo).
        self.collection.create_index(
            [("empresa_id", ASCENDING), ("tipo", ASCENDING), ("clave", ASCENDING)],
            name="valor_unico",
            unique=True,
        )

    def listar(self, empresa_id: str, tipo: str) -> list:
        """Los valores de ese catálogo, en orden alfabético."""
        documentos = self.collection.find({"empresa_id": empresa_id, "tipo": tipo}, {"valor": 1})
        return sorted((doc["valor"] for doc in documentos), key=_orden_alfabetico)

    def registrar(self, empresa_id: str, tipo: str, valor: str) -> None:
        """Agrega el valor al catálogo si todavía no está. Si ya existe (con otras mayúsculas u
        otros espacios) no cambia nada: se conserva como se escribió la primera vez. Un valor vacío
        no se guarda.

        Es una sola operación en MongoDB (upsert), así que dos peticiones con el mismo valor al
        tiempo dejan un solo documento."""
        clave = clave_de(valor)
        if not clave:
            return
        filtro = {"empresa_id": empresa_id, "tipo": tipo, "clave": clave}
        try:
            self.collection.update_one(filtro, {"$setOnInsert": {"valor": limpiar_valor(valor)}}, upsert=True)
        except DuplicateKeyError:
            # Dos upsert simultáneos pueden intentar insertar ambos; el índice único rechaza al
            # segundo. El valor ya quedó guardado por el primero, que es lo que se quería.
            pass
