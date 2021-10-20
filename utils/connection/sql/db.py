from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from main import config

engine = create_engine(config.db.sql)

db = sessionmaker(bind=engine)

def get_sqldb():
    d = db()
    try:
        yield d
    finally:
        d.close()