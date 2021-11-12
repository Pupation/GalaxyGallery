import enum

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Enum, DateTime, BigInteger, Boolean, SmallInteger, Numeric, BINARY, Text
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from sqlalchemy.sql import func
from sqlalchemy.future import select
from datetime import datetime
from typing import Optional, List, Any, Dict
from bson import ObjectId
from fastapi import HTTPException
from math import floor, ceil

from models.torrent.collection import CollectionItems, Collection, get_collections_by_tids

from .. import Base
from .peer import get_peer_count
from utils.cache import gg_cache, evict_cache_keyword
from utils.connection.sql.db import get_sqldb
from utils.connection.nosql.db import client
from utils.provider.size_parser import parse_size
from main import config

from pydantic import BaseModel


class TorrentStatus(enum.Enum):
    normal = 0
    ban = 1
    pending = 2  # voting
    archive = 3


class PromotionStatus(enum.Enum):
    normal = 0
    double = 1
    three_seconds = 2  # 1.5x
    free = 3


class PopStatus(enum.Enum):
    normal = 0
    top = 1
    doubletop = 2
    tripletop = 3
    quadratop = 4
    pentatop = 5


class TorrentSQL(Base):
    __tablename__ = 'torrents'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    status = Column(Enum(TorrentStatus), nullable=False,
                    default=TorrentStatus.pending)
    record_id = Column(String(32), nullable=True, index=True, primary_key=True)
    rank_by = Column(DateTime, default=datetime.now())
    added = Column(DateTime, default=datetime.now())
    modified = Column(DateTime, default=datetime.now())
    last_seed = Column(DateTime, default=datetime.now())
    finished = Column(SmallInteger, nullable=False, default=0)
    category = Column(SmallInteger, nullable=False, default=0)
    owner_id = Column(Integer, nullable=True, default=0)
    anonymous = Column(Boolean, default=False, nullable=False)
    size = Column(BigInteger, nullable=False, default=0)
    info_hash = Column(BINARY(20), nullable=False,
                       default=b'0'*20, unique=True)
    info_hash_plain = Column(BINARY(20), nullable=False,
                             default=b'0'*20, unique=True)
    numfiles = Column(SmallInteger, nullable=False, default=0)
    name = Column(Text, nullable=False, default='')
    subname = Column(Text, nullable=False, default='')
    hits = Column(Integer, nullable=False, default=0)
    upload_promo = Column(Enum(PromotionStatus),
                          nullable=False, default=PromotionStatus.normal)
    upload_until = Column(DateTime, nullable=True)
    download_promo = Column(Enum(PromotionStatus),
                            nullable=False, default=PromotionStatus.normal)
    download_until = Column(DateTime, nullable=True)
    popstatus = Column(Enum(PopStatus), nullable=False,
                       default=PopStatus.normal)
    popuntil = Column(DateTime, nullable=True)
    vote_up = Column(SmallInteger, nullable=True, default=0)
    vote_down = Column(SmallInteger, nullable=True, default=0)


class TorrentNoSQL(BaseModel):
    _id: Optional[ObjectId]
    filename: Optional[str]
    desc: str
    info_hash: bytes
    torrent: Optional[bytes]
    detail: Dict[str, Any]


def flush_page_cache():
    asyncio.create_task(evict_cache_keyword(
        "{_get_torrent_list.__module__}.{_get_torrent_list.__name__}"))


@gg_cache(cache_type='timed_cache')
async def _get_torrent_list(page, keyword, cid=None):
    ret = []
    async for db in get_sqldb():
        query = select(TorrentSQL).where(
            TorrentSQL.status == TorrentStatus.normal)
        # query = db.query(TorrentSQL).filter(TorrentSQL.status == TorrentStatus.normal)
        if keyword:
            query = query.where(func.concat(
                TorrentSQL.name, TorrentSQL.subname).like(f"%{keyword}%"))
        if cid:
            query = query.join(CollectionItems, CollectionItems.tid ==
                               TorrentSQL.id, isouter=False).where(CollectionItems.cid == cid)
        query = query.order_by(TorrentSQL.popstatus.desc(),
                               TorrentSQL.rank_by.desc())
        total = (await db.execute(query.with_only_columns(func.count()))).scalar()
        if cid is None:
            if page * config.site.preference.per_page > total:
                # redirect to taht page number
                return floor(total / config.site.preference.per_page), total
            query = query.offset(
                page * config.site.preference.per_page
            ).limit(
                config.site.preference.per_page
            )
        for t, in (await db.execute(query)).all():
            ret.append(
                {
                    'id': t.id,
                    'name': t.name,
                    'subname': t.subname,
                    'downloaded': t.finished,
                    'size': parse_size(t.size),
                    'info_hash': t.info_hash,
                    'rank_by': t.rank_by,
                    'added': t.added
                }
            )
    return ret, total


@gg_cache(cache_type='timed_cache')
async def get_torrent_list(page: int = 0, keyword: str = None, version=None):
    db: AsyncSession
    ret, total = await _get_torrent_list(page, keyword)
    if isinstance(ret, int):
        return await get_torrent_list(ret, keyword, version)
    if version == 'v1':
        for record in ret:
            info_hash = record['info_hash']
            record.update(** await get_peer_count(info_hash))
        return {'data': ret,
                'page': page,
                'total': ceil(total / config.site.preference.per_page)
                }
    elif version == 'v2':
        from models.forms.torrent import TorrentListResponse
        tids = [t['id'] for t in ret]
        t_c_maps = [-1] * len(tids)
        viewed = []
        warpped_torrents = []
        collections: List[Collection] = await get_collections_by_tids(tids)
        for c_idx, c in enumerate(collections):
            for item in c.items:
                try:
                    t_c_maps[tids.index(item.torrent.id)] = c_idx
                except:
                    pass

        for cur, c_idx in enumerate(t_c_maps):
            if c_idx == -1:
                warpped_torrent = TorrentListResponse.CollectionBreifResponse(
                    **{
                        'id': -1,
                        'name': 'N/A',
                        'subname': 'N/A',
                        'rank_by': ret[cur]['rank_by'],
                        'torrents': [
                                {
                                    **ret[cur],
                                    ** await get_peer_count(ret[cur]['info_hash']),
                                    'entry_name': ret[cur]['name'],
                                    'added': ret[cur]['added'],
                                }
                        ],
                        # FIXME: Placeholder poster
                        'poster': 'https://img9.doubanio.com/view/photo/l_ratio_poster/public/p2687443734.jpg'
                    }
                )
            else:
                if c_idx in viewed:
                    continue
                in_collection = TorrentListResponse.CollectionBreifResponse.InCollectionBreifResponse
                viewed.append(c_idx)
                coll = collections[c_idx]
                warpped_torrent = TorrentListResponse.CollectionBreifResponse(
                    **{
                        'id': coll.id,
                        'name': coll.name,
                        'subname': coll.subname,
                        'rank_by': ret[cur]['rank_by'],
                        'torrents': [],
                        # FIXME: Placeholder poster
                        'poster': 'https://img9.doubanio.com/view/photo/l_ratio_poster/public/p2687443734.jpg'
                    }
                )
                warpped_torrent.torrents = [
                    in_collection(
                        **await get_peer_count(item.torrent.info_hash),
                        downloaded=item.torrent.finished,
                        entry_name=item.desc,
                        size=parse_size(item.torrent.size),
                        id=item.torrent.id,
                        rank_by=item.torrent.rank_by,
                        added=item.torrent.added
                    )
                    for item in coll.items
                ]
                # warpped_torrent.torrents = (await get_torrent_list(cid=coll.id))['data']
                print(warpped_torrent)

            warpped_torrents.append(warpped_torrent)

        return {
            "total": ceil(total / config.site.preference.per_page),
            "page": page,
            "data": warpped_torrents
        }


@gg_cache
async def get_torrent_info_hash(torrent_id):
    db: AsyncSession
    async for db in get_sqldb():
        try:
            sql = select(TorrentSQL).where(TorrentSQL.id == torrent_id)
            record = await db.execute(sql)
            record, = record.first()
            return record.info_hash
        except:
            raise HTTPException(404, 'Torrent does not exsit')


@gg_cache
async def get_torrent_id(torrent_info_hash):
    db: AsyncSession
    async for db in get_sqldb():
        try:
            sql = select(TorrentSQL).where(
                TorrentSQL.info_hash == torrent_info_hash)
            record = await db.execute(sql)
            record, = record.first()
            return record.id
        except:
            raise HTTPException(404, 'Torrent does not exsit')


async def get_torrent_detail(torrent_id: int, torrent: int):
    info_hash = await get_torrent_info_hash(torrent_id)
    projection = {'_id': 0,
                  'torrent': torrent,
                  'info_hash': 1, 'desc': 1, 'detail': 1, 'filename': 1}
    for key in list(projection.keys()):
        if projection[key] == 0:
            projection.pop(key)

    ret = client.torrents.find(
        {'info_hash': info_hash},
        projection
    )
    print(ret)
    for r in await ret.to_list(1):
        record = dict(TorrentNoSQL(**r))
        return record

    return None
