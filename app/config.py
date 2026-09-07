import os


class Config:
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "taskmanager")
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"
