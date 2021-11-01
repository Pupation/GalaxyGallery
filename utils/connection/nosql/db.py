from main import config

from pymongo import MongoClient
import motor.motor_asyncio

client = motor.motor_asyncio.AsyncIOMotorClient(config.db.nosql.url, serverSelectionTimeoutMS=5000).__getattr__(config.db.nosql.name)

_client = MongoClient(config.db.nosql.url).__getattr__(config.db.nosql.name)