from .. import Base
from sqlalchemy import Integer, Column, ForeignKey, Enum, DateTime, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
import enum
from pydantic import BaseModel
from typing import List

from utils.cache import gg_cache
from utils.connection.sql.db import get_sqldb

class UserSeedStatus(enum.Enum):
    DOWNLOADING = 0
    SEEDING = 1
    PARTICAL_SEEDING = 2

class UserPeerStat(Base):
    __tablename__ = 'user_peer_stats'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    uid = Column(Integer,ForeignKey('users.id'), primary_key=True, index=True)
    tid = Column(Integer,ForeignKey('torrents.id'), primary_key=True, index=True)
    status = Column(Enum(UserSeedStatus), default=UserSeedStatus.DOWNLOADING)
    started = Column(DateTime, default=datetime.now())
    leechtime = Column(Integer, default=0)
    seedtime = Column(Integer, default=0)
    uploaded = Column(BigInteger, default=0)
    downloaded = Column(BigInteger, default=0)
    left = Column(Integer, default=0)
    torrent_size = Column(BigInteger, default=0)
    measured_uploaded_speed = Column(Integer, default=0)
    measured_downloaded_speed = Column(Integer, default=0)
    last_action = Column(DateTime, onupdate=func.current_timestamp())

class UserPeerStatRecord(BaseModel):
    username: str
    status: str
    leechtime: int
    seedtime: int
    uploaded: int
    downloaded: int
    last_action: datetime
    started: datetime
    measured_downloaded_speed: int
    measured_uploaded_speed: int
    left: int

class UserPeerStatResponse(BaseModel):
    data: List[UserPeerStatRecord]
    total: int

class UserPeerStatCountResponse(BaseModel):
    seeding: int = 0
    downloading: int = 0
    partial_seed: int = 0

@gg_cache(cache_type='timed_cache')
async def get_last_action(tid):
    db: AsyncSession
    async for db in get_sqldb():
        try:
            sql = select(func.max(UserPeerStat.last_action).label('last_action')).where(UserPeerStat.tid==tid, UserPeerStat.status==UserSeedStatus.SEEDING)
            result, = (await db.execute(sql)).first()
            print(result)
            return result
        except:
            return datetime.now()
        finally:
            await db.close()

@gg_cache(cache_type='timed_cache')
def get_count_peer_stat_count_by_tid(torrent_id: int):
    for db in get_sqldb():
        result = db.query(UserPeerStat.status, func.count(UserPeerStat.status)).filter(
            (UserPeerStat.tid == torrent_id) &
            (UserPeerStat.last_action > datetime.utcnow() - timedelta(minutes=30))
            ).group_by(UserPeerStat.status).all()
    ret = dict()
    for r,v in result:
        ret[r.name.lower()] = v
    return ret

@gg_cache(cache_type='timed_cache')
def get_count_peer_stat_count_by_uid(uid: int):
    for db in get_sqldb():
        query = db.query(UserPeerStat.status, func.count(UserPeerStat.status)).filter(
            (UserPeerStat.uid == uid) &
            (UserPeerStat.last_action > datetime.now() - timedelta(minutes=30))
            ).group_by(UserPeerStat.status)
        print(str(query))
        result = query.all()
    ret = dict()
    for r,v in result:
        ret[r.name.lower()] = v
    return ret