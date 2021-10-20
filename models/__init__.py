from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def create_all():
    from utils.connection.sql.db import engine
    Base.metadata.create_all(bind=engine)