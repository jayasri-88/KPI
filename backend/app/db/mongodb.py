from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.core.config import settings


client = MongoClient(
    settings.mongodb_url,
    serverSelectionTimeoutMS=10000
)

database = client[settings.mongodb_database]


def get_database():
    return database


def ping_database():
    try:
        client.admin.command("ping")
        return True
    except PyMongoError:
        return False