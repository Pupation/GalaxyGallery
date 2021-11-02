from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Table

Base: Table = declarative_base()


async def create_all():
    from utils.connection.sql.db import engine
    from utils.connection.sql.db import get_sqldb
    # Base.metadata.create_all(bind=engine)

    from .user.role import Role
    async with engine.begin() as db:
        await db.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as db:
        try:
            db.add_all([
                Role(role_name='unconfirmed', admin=False, permissions=1),
                Role(role_name='admin', admin=True, permissions=0),
                Role(role_name='newbie', admin=False, permissions=1),
                Role(role_name='{customize}', admin=False, permissions=0)
            ])
            await db.commit()
        except:
            pass
        finally:
            await db.close()
    return {'ok': 1}


class GeneralResponse(BaseModel):
    ok: int = 1
