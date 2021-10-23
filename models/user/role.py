from datetime import datetime
from .. import Base

from sqlalchemy import Integer, Column, String, Boolean, Table, ForeignKey, DateTime, SmallInteger
from sqlalchemy.orm import relationship

class Permission(Integer):
    LOGIN = 0x1
    UPLOAD = 0x2
    UPLOAD_TORRENT = 0x4
    BYPASS_VOTE_TORRENT = 0x8
    DOWNLOAD_TORRENT = 0x10

    NO_LEECH = 0x1000000
    NO_SEED  = 0x2000000


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def has(self, permission: int):
        return int(self) & permission
    
    def set(self, permission: int):
        self = self & permission
    
    def revoke(self, permission: int):
        self = self & ~permission

class URMap(Base):
    __tablename__ = 'users_roles_map'
    uid = Column(Integer, ForeignKey('users.id'), primary_key=True)
    rid = Column(SmallInteger, ForeignKey('roles.id'), primary_key=True)
    role = relationship("Role", lazy="joined")
    priority = Column(SmallInteger, default=0)
    expire = Column(DateTime, default=None)
    payload = Column(String(128), nullable=True)

class Role(Base):
    __tablename__ = 'roles'
    id = Column(SmallInteger, primary_key=True, nullable=False,
                autoincrement=True, unique=True)
    role_name = Column(String(128), nullable=True, unique=True)
    # overrides all permissions
    admin = Column(Boolean, nullable=True, default=False)
    permissions = Column(Permission, nullable=True, default=0)
    selfenroll = Column(Boolean, nullable=False, default=True)
    color = Column(Integer, nullable=False, default=0x00ff00)

    def has_permission(self, permission: int):
        if permission < 0x1000000:
            return self.admin or (self.permissions & permission)
        else:
            return self.permissions & permission
