from main import config

from pymongo import MongoClient

client = MongoClient(config.db.nosql.url).__getattr__(config.db.nosql.name)



