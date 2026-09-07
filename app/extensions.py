from pymongo import MongoClient

_client = None
_db = None


def init_db(app):
    global _client, _db
    _client = MongoClient(app.config["MONGO_URI"])
    _db = _client[app.config["MONGO_DB_NAME"]]
    return _db


def get_db():
    if _db is None:
        raise RuntimeError("La base de datos no ha sido inicializada. Llama a init_db(app) primero.")
    return _db
