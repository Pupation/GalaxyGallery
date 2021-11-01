from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table

Base:Table = declarative_base()

def create_all():
    from utils.connection.sql.db import engine
    from utils.connection.sql.db import get_sqldb
    Base.metadata.create_all(bind=engine)

    from .user.role import Role
    for db in get_sqldb():
        db.add(Role(role_name='unconfirmed', admin=False, permissions=1))
        db.add(Role(role_name='admin', admin=True, permissions=0))
        db.add(Role(role_name='newbie', admin=False, permissions=1))
        db.add(Role(role_name='{customize}', admin=False, permissions=0))
        db.commit()
        db.close()


from pydantic import BaseModel

class GeneralResponse(BaseModel):
    ok: int = 1