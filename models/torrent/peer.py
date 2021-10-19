
from pydantic import BaseModel
from typing import Optional, Union, List
from bson import ObjectId
from datetime import datetime, timedelta

from struct import pack
from socket import inet_pton, AF_INET, AF_INET6

from utils.connection.nosql.db import client as nosql_client
from utils.cache import gg_cache
from models.helper import ErrorException, IP



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
            self.peer.seeder = seeder
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
                    "seeder": seeder
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
    def __init__(self, seeder: bool, info_hash: bytes, requester_ip: IP,compact:bool = False) -> List[Peer]:
        query_params = {
                "info_hash": info_hash,
                "to_go": { "$gt": datetime.now() },
                "$or": []
            }
        result_projection = {
            "port": 1
        }
        self.has_ipv4 = requester_ip.has_ipv4()
        self.has_ipv6 = requester_ip.has_ipv6()
        if self.has_ipv4:
            query_params['$or'].append({ 'ipv4': { "$nin": [None, requester_ip.ipv4]}})
            result_projection['ipv4'] = 1
        if self.has_ipv6:
            query_params['$or'].append({ 'ipv6': { "$nin": [None, requester_ip.ipv6]}})
            result_projection['ipv6'] = 1
        
        if seeder:
            query_params['seeder'] = False
        self.records = nosql_client.peers.find(query_params, result_projection)
        self.compact = compact
        self.seeder = seeder
        
    def __call__(self, num_want=40): # TODO: num_want
        ret_v4 = []
        ret_v6 = []
        if self.has_ipv4:
            for record in self.records:
                ipv4 = record.get('ipv4', None)
                if ipv4 is None:
                    continue
                ret_v4.append({'ip': ipv4, 'port': record.get('port')})
        if self.has_ipv6:
            for record in self.records:
                ipv6 = record.get('ipv6', None)
                if ipv6 is None:
                    continue
                ret_v6.append({'ip': ipv6, 'port': record.get('port')})     
        if self.compact:
            pack_v4 = lambda r: inet_pton(AF_INET, r['ip']) + pack(">H", r['port'])
            pack_v6 = lambda r: inet_pton(AF_INET6, r['ip']) + pack(">H", r['port'])
            return {
                'peers': b''.join([pack_v4(r) for r in ret_v4]),
                'peers6': b''.join([pack_v6(r) for r in ret_v6])
            }
        else: # not compact
            return {'peers': ret_v4 + ret_v6}

    def __len__(self):
        return len(self.records)
    

@gg_cache(cache_type='timed_cache')
def get_peer_count(info_hash: bytes):
    query_params = {
        "info_hash": info_hash,
        "to_go": { "$gt": datetime.now() }
    }
    counts = nosql_client.peers.aggregate(
        [{"$match": query_params}, 
         {"$group": 
            {"_id": "$seeder", 
            "count": {"$sum": 1}}
         }
        ])
    ret = {
        'incomplete': 0,
        'complete': 0
    }
    for c in counts:
        if c['_id'] == False:
            ret['incomplete'] = c['count']
        else:
            ret['complete'] = c['count']
    return ret
