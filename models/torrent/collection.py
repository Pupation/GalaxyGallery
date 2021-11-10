from .. import Base

from sqlalchemy import Integer, Text, DateTime, Column, SmallInteger, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

import enum

from utils.cache import gg_cache
from utils.connection.sql.db import get_sqldb

class CategorySource(enum.Enum):
    user = 0
    official = 1
    awards = 2
    recommendations = 3

class CategoryPublished(enum.Enum):
    private = 0
    friends_only = 1
    public = 2


class Collection(Base):
    id = Column(Integer, primary_key=True, index=True, default=func._nextval('uid_cid'))
    source = Column(Enum(CategorySource), default=CategorySource.user)
    published = Column(Enum(CategoryPublished), default=CategoryPublished.private)
    desc = Column(Text, nullable=True)
    owner_id = Column(Integer, nullable=False)
    tags = Column(Text, nullable=False)
    category = Column(SmallInteger, nullable=True)
    created = Column(DateTime, nullable=False)
    last_modified = Column(DateTime, nullable=False, onupdate=func.current_timestamp())
    hit = Column(Integer, nullable=False, default=0)
    torrents = relationship('CollectionItems', foreign_keys='torrents.id')
            

class CollectionItems(Base):
    id = Column(Integer, primary_key=True, autoincrement=True)
    tid = Column(Integer, ForeignKey('torrents.tid'), nullable=False, index=True)
    cid = Column(Integer, nullable=False, index=True)
    added_time = Column(DateTime, nullable=False, default=func.current_timestamp())

async def add_to_collection(collection, db: AsyncSession, tid: int):
    # Here the collection could be an instance of Collection or user
    row = CollectionItems(cid = collection.id, tid = tid)
    db.add(row)
    await db.commit()
    await db.refresh(row)

async def delete_from_collection(collection, db: AsyncSession, record_id: int):
    sql = select(CollectionItems).where(CollectionItems.id == record_id)
    record = (await db.execute(sql)).first()
    await db.delete(record)
    await db.commit()

@gg_cache(cache_type='timed_cache')
async def in_collection(self, cid:int, tids: List[int]):
    sql = select(CollectionItems.id).where(CollectionItems.tid.in_(tids))
    result = [0] * len(tids)
    async for db in get_sqldb():
        ret = await db.execute(sql)
        for record, in ret:
            result[tids.index(record)] = 1
        