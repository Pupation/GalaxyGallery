import enum
import time
import random
from hashlib import sha256, md5
from typing import Any

from sqlalchemy import Column, Integer, String, Enum, DateTime, BigInteger, Boolean, SmallInteger, Numeric, BINARY
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime

from .. import Base
from ..helper import GeneralException

from utils.cache import gg_cache
from utils.connection.sql.db import db as sqldb

class UserStatus(enum.Enum):
    pending = 1
    confirmed = 2
    needverify = 3

class UserPrivacy(enum.Enum):
    strong = 1
    normal = 2
    low = 3

class UserGender(enum.Enum):
    male = 1
    female = 2
    na = 3

class UserAccept(enum.Enum):
    yes = 1
    friends = 2
    no = 3

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    username = Column(String(40), nullable=False, default='', unique=True)
    passhash = Column(BINARY(35), nullable=False, default='')
    passkey = Column(String(32), nullable=False, default='')
    secret = Column(String(20), nullable=False, default='')
    email = Column(String(128), nullable=False, default='')
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.pending)
    join = Column(DateTime, nullable=False, default=datetime.now())
    role = Column(SmallInteger, nullable=False, default=0)

    last_login = Column(DateTime, nullable=False, default=datetime.now())
    last_access = Column(DateTime, nullable=False, default=datetime.now())
    editsecret = Column(String(20), nullable=False, default='')
    privacy = Column(Enum(UserPrivacy), nullable=False, default=UserPrivacy.normal)
    stylesheet = Column(Integer, nullable=False, default=1)

    record_id = Column(String(32), nullable=True, default='')
    uploaded = Column(BigInteger, nullable=False, default=0)
    downloaded = Column(BigInteger, nullable=False, default=0)
    seedtime = Column(BigInteger, nullable=False, default=0)
    leechtime = Column(BigInteger, nullable=False, default=0)

    enabled = Column(Boolean, nullable=False, default=True)
    warned = Column(Boolean, nullable=False, default=False)
    warneduntil = Column(DateTime, nullable=True)

    lang = Column(SmallInteger, nullable=False, default=0)

    invites = Column(SmallInteger, nullable=False, default=0)
    invited_by = Column(Integer, nullable=False, default=0)

    gender = Column(Enum(UserGender), nullable=False, default=UserGender.na)
    renamenum = Column(SmallInteger, nullable=False, default=0)
    school = Column(SmallInteger, nullable=False, default=0)
    hnr_score = Column(Numeric(precision=6, scale=3), nullable=False, default=100.000)

    acceptpms = Column(Enum(UserAccept), nullable=False, default= UserAccept.yes)
    commentpm = Column(Enum(UserAccept), nullable=False, default= UserAccept.yes)
    acceptatpms = Column(Enum(UserAccept), nullable=False, default= UserAccept.yes)

    @staticmethod
    def gen_secret(length=20) -> str:
        random.seed(time.time())
        return ''.join(map(chr, random.choices(range(60, 122), k=length)))

    @staticmethod
    def get_passhash(secret, password, method='sha256') -> bytes:
        v = (secret+password+secret).encode('utf-8')
        if method == 'sha256':
            return b'sha'+ sha256(v).digest()
        if method == 'md5':
            return b'md5'+ md5(v).digest()
        
    def validate_password(self, password) -> bool:
        if self.passhash[:3] == b'sha':
            passhash = User.get_passhash(self.secret, password)
        elif self.passhash[:3] == b'md5':
            passhash = User.get_passhash(self.secret, password, 'md5')
        else:
            raise GeneralException('Password invalid, please contact administrator.', 500)
        return passhash == self.passhash
    
    @staticmethod
    def login(db:Session, username, password):
        user = db.query(User).filter(User.username == username).one()
        if user.validate_password(password):
            user.last_login = datetime.now()
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        else:
            raise GeneralException("Username or password wrong", 404)
    
    def get_profile(self, bypass_privacy=True):
        rep = dict()
        to_return = []
        if bypass_privacy or self.privacy in [UserPrivacy.strong, UserPrivacy.normal, UserPrivacy.low]:
            to_return += ['username']

        if bypass_privacy or self.privacy in [UserPrivacy.normal, UserPrivacy.low]:
            to_return += ['role','uploaded','seedtime', 'leechtime','gender']

        if bypass_privacy or self.privacy in [UserPrivacy.low]:
            to_return += ['email']

        for key in to_return:
            rep[key] = self.__getattribute__(key)

        return rep
        

@gg_cache(cache_type='timed_cache') # TODO: need sophisticated cache to improve performance
def get_user_by_id(uid, bypass_cache: Any=None): 
    del bypass_cache
    db:Session = sqldb()
    return db.query(User).filter(User.id == uid).one()