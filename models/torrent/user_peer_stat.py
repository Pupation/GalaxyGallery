from .. import Base
from sqlalchemy import Integer, Column, ForeignKey, Enum, DateTime, BigInteger
from sqlalchemy.sql import func
from datetime import datetime
import enum

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