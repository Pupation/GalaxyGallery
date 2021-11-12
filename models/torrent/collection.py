import enum
from typing import List, Union

from sqlalchemy import (Column, DateTime, Enum, ForeignKey, Integer,
                        SmallInteger, Text)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from utils.cache import gg_cache
from utils.connection.sql.db import get_sqldb

from .. import Base


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
    _tags = Column("tags", Text, nullable=False)
    category = Column(SmallInteger, nullable=True)
    created = Column(DateTime, nullable=False, default=func.current_timestamp())
    last_modified = Column(DateTime, nullable=False,default=func.current_timestamp(),
                           onupdate=func.current_timestamp())
    hit = Column(Integer, nullable=False, default=0)
    items = relationship(
        'CollectionItems', primaryjoin='foreign(Collection.id) == remote(CollectionItems.cid)', lazy='joined',
        uselist=True
    )

    @property
    def tags(self) -> List:
        return eval(self._tags)
    
    @tags.setter
    def tags(self, tags):
        self._tags = str(tags)

    def append_tags(self, tag):
        tags = self.tags
        tags.append(tag)
        self.tags = tags


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
    db: AsyncSession
    if isinstance(tids, int):
        tids = [tids]
    sql = select(Collection).where(
        Collection.items.any(CollectionItems.tid.in_(tids)) & (Collection.source == c_type))
    result = []
    # print(sql)
    # sql = "select * from collections inner join collection_items on collections.id = collection_items.cid inner join torrents on torrents.id = collection_items.tid where torrents.id in :tids and collections.source = :source;"
    async for db in get_sqldb():
        ret = await db.execute(sql, params={
            "tids": tuple(tids),
            "source": c_type.name
        })
        for coll, in ret.unique().all():
            # print(coll.name, colli.desc, t.subname)
            # print(coll)
            print(coll.__dict__, coll.items, [(i.desc, i.torrent.subname) for i in coll.items])
            result.append(coll)
    return result
