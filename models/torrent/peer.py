
from pydantic import BaseModel
from typing import Optional, Union
from bson import ObjectId
from datetime import datetime

from struct import pack
from socket import inet_pton, AF_INET, AF_INET6

class Peer:
    def __init__(self, **kwargs):
        self.peer = PeerModel(**kwargs)
    
    def __call__(self, compact:bool, ip_version: int = 4) -> Union[dict, bytes]:
        ip_address = self.peer.__getattribute__('ipv%d' % ip_version)
        if compact:
            return {
                "ip": ip_address,
                "port": self.peer.port
            }
        else:
            if ip_version == 4:
                packed = inet_pton(AF_INET, ip_address)
            else:
                packed = inet_pton(AF_INET6, ip_address)
            return packed + pack("H", self.peer.port)
        
    

class PeerModel(BaseModel):
    _id: ObjectId
    torrent: int
    seeder: bool
    peer_id: bytes
    ipv6: Optional[str]
    ipv4: Optional[str]
    port: int
    downloaded: Optional[int]
    uploaded: Optional[int]
    to_go: Optional[int]
    started: datetime
    last_action: datetime
    prev_action: datetime
    userid: int
    agent: bytes
    finishedat: Optional[int]
    downloadoffset: Optional[int]
    uploadoffset: Optional[int]
    passkey: str
    requirecrypto: Optional[bool]
    supportcrypto: Optional[bool]
