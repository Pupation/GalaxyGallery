
from pydantic import BaseModel
from typing import Optional, Union, List
from bson import ObjectId
from datetime import datetime, timedelta

from struct import pack
from socket import inet_pton, AF_INET, AF_INET6

from utils.connection.nosql.db import client as nosql_client
from models.helper import ErrorException


class PeerModel(BaseModel):
    _id: Optional[ObjectId]
    torrent: Optional[int]
    info_hash: Optional[bytes]
    seeder: Optional[bool]
    peer_id: Optional[bytes]
    ipv6: Optional[str]
    ipv4: Optional[str]
    port: Optional[int]
    downloaded: Optional[int]
    uploaded: Optional[int]
    to_go: Optional[datetime]
    started: Optional[datetime]
    last_action: Optional[datetime]
    prev_action: Optional[datetime]
    userid: Optional[int]
    agent: Optional[bytes]
    finishedat: Optional[int]
    downloadoffset: Optional[int]
    uploadoffset: Optional[int]
    passkey: Optional[str]
    requirecrypto: Optional[bool]
    supportcrypto: Optional[bool]


class Peer:
    def __init__(self, event='', **kwargs):
        self.request = kwargs
        self.time = datetime.now()
        self.event = event
        if event == 'started':
            self.created = True
            self.peer = PeerModel(**kwargs)
            self.peer.started = self.time
        else:
            self.peer = Peer._get_active_record(**kwargs)
            self.created = False
            if self.peer is not None:
                self.objectId = self.peer['_id']
                self.peer = PeerModel(**self.peer)
            else:
                # FIXME: Mingjun: I guess we should not create new peer for this event?
                # Basically, this event is a periodically reporting labeled with str("")
                self.created = True
                self.peer = PeerModel(**kwargs)
                self.peer.started = self.time
        # if event != 'started':
        #     self.created = False
        #     else:
        #         raise ErrorException("Not record found for the specified peer.")


    def __call__(self, compact: bool, ip_version: int = 4) -> Union[dict, bytes]:
        ip_address = self.peer.__getattribute__('ipv%d' % ip_version)
        if not compact:
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
    
    def commit(self, next_allowance: timedelta = timedelta(minutes=30), seeder=False):
        if self.created:
            self.peer.prev_action = self.peer.last_action
            self.peer.last_action = datetime.now()
            self.peer.to_go = self.peer.last_action + next_allowance
            nosql_client.peers.insert_one(dict(self.peer))
        else:
            nosql_client.peers.find_one_and_update(
                {"_id": self.objectId},
                {'$set': {
                    "prev_action": self.peer.last_action,
                    "last_action": self.time,
                    "to_go": self.time + next_allowance,
                    "downloaded": self.request["downloaded"],
                    "uploaded": self.request["uploaded"],
                }}
            )

    @staticmethod
    def _get_active_record(**kwargs) -> dict:
        return nosql_client.peers.find_one({
            "info_hash": kwargs.get("info_hash"),
            "to_go": { "$gt": datetime.now() },
            "passkey": kwargs.get("passkey"),
            "port": kwargs.get("port")
        })
    


class PeerList:
    # @staticmethod
    def __call__(self, seeder: bool, info_hash: bytes, ip_version: int, requester_ip: str,compact:bool = False) -> List[Peer]:
        query_params = {
                "info_hash": info_hash,
                "to_go": { "$gt": datetime.now() },
                f"ipv{ip_version}": { "$nin": [None, requester_ip] }
            }
        if seeder:
            query_params['seeder'] = False
        peers = nosql_client.peers.find(query_params, {
            f"ipv{ip_version}": 1,
            "port": 1
        })
        if not compact:
            return [{
                "ip": record.get('ipv%d' % ip_version),
                "port": record["port"]
            } for record in peers]
        else: # Compact
            array = []
            _AF_NET = AF_INET if ip_version == 4 else AF_INET6
            for record in peers:
                try:
                    array.append( 
                        inet_pton(_AF_NET, record[f"ipv{ip_version}"]) + \
                        pack(">H", record["port"])
                    )
                except:
                    print(record, type(record))

            return b''.join(array) 
