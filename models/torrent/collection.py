from .. import Base

from sqlalchemy import Integer, Text, DateTime, Column, SmallInteger, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Union

import enum

from utils.cache import gg_cache
from utils.connection.sql.db import get_sqldb


class CollectionSource(enum.Enum):
    user = 0
    official = 1
    awards = 2
    recommendations = 3
    group = 4


class CategoryPublished(enum.Enum):
    private = 0
    friends_only = 1
    public = 2


class Collection(Base):
    __tablename__ = 'collections'
    id = Column(Integer, primary_key=True, index=True,
                default=func._nextval('uid_cid'))
    name = Column(Text, nullable=False)
    subname = Column(Text, nullable=False)
    source = Column(Enum(CollectionSource), default=CollectionSource.user)
    published = Column(Enum(CategoryPublished),
                       default=CategoryPublished.private)
    desc = Column(Text, nullable=True)
    owner_id = Column(Integer, nullable=False)
    tags = Column(Text, nullable=False)
    category = Column(SmallInteger, nullable=True)
    created = Column(DateTime, nullable=False)
    last_modified = Column(DateTime, nullable=False,
                           onupdate=func.current_timestamp())
    hit = Column(Integer, nullable=False, default=0)
    items = relationship(
        'CollectionItems', primaryjoin='foreign(Collection.id) == remote(CollectionItems.cid)', lazy='joined',
        uselist=True
    )

class CollectionItems(Base):
    __tablename__ = 'collection_items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tid = Column(Integer, ForeignKey('torrents.id'),
                 nullable=False, index=True)
    cid = Column(Integer, nullable=False, index=True)
    desc = Column(Text, nullable=True)
    added_time = Column(DateTime, nullable=False,
                        default=func.current_timestamp())
    torrent = relationship('TorrentSQL', lazy='joined')


async def add_to_collection(collection, db: AsyncSession, tid: int, desc: str = ''):
    # Here the collection could be an instance of Collection or user
    row = CollectionItems(cid=collection.id, tid=tid, desc=desc)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def delete_from_collection(collection, db: AsyncSession, record_id: int):
    sql = select(CollectionItems).where(CollectionItems.id == record_id)
    record = (await db.execute(sql)).first()
    await db.delete(record)
    await db.commit()


@gg_cache(cache_type='timed_cache')
async def in_collection(self, cid: int, tids: List[int]):
    sql = select(CollectionItems.id).where(CollectionItems.tid.in_(tids))
    result = [0] * len(tids)
    async for db in get_sqldb():
        ret = await db.execute(sql)
        for record, in ret:
            result[tids.index(record)] = 1


async def get_collections_by_tids(tids: Union[List[int], int], c_type: CollectionSource = CollectionSource.group):
    if isinstance(tids, int):
        tids = [tids]
    sql = select(Collection).where(
        CollectionItems.tid.in_(tids) & (Collection.source == c_type))
    print(sql)
    async for db in get_sqldb():
        ret = await db.execute(sql)
        for coll, in ret.unique().all():
            # print(coll.name, colli.desc, t.subname)
            print(coll.__dict__, coll.items, [(i.desc, i.torrent.subname) for i in coll.items])
