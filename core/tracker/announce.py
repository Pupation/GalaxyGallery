from fastapi import Header, Request
from datetime import timedelta

from main import gg
from utils.response import BencResponse, ErrorResponse
from utils.checker import check_ip, check_ua_or_400, check_port_or_400
from models.helper import ErrorException, IP
from models.torrent import Peer, PeerList, get_peer_count

@gg.get('/announce')
async def announce(
    request: Request,

    port: int, passkey: str, info_hash: bytes,
    peer_id: str, key: str, uploaded: int, downloaded: int, left: int,
    compact: int = 0, no_peer_id: int = 0,
    event: str = '',
    supportcrypto: bool = False, requirecrypto: bool = False,
    ipv6: str = None
):
    if event not in ['started', 'completed', 'stopped', 'paused', '']:
        return ErrorResponse('Unknown event.')
    # print(info_hash, peer_id)
    ip = IP(request.client.host, ipv6) # FIXME: get ip
    
    # print(request.headers)
    # FIXME: BEAWARE DoS! Blocked ip address still able to consume server computation resource
    try:

        coroutine_checkip = check_ip(ip)

        torrent_client = check_ua_or_400(request)
        check_port_or_400(port)
        blocked_ip = await coroutine_checkip
        if blocked_ip:
            raise ErrorException('Blocked IP.')

        rep_dict = {
            "interval": 60,
            "min interval":  10,
            # "complete": 20,
            # "incomplete": 10
            # "peers" : None  # By default it is a array object, only when `&compact=1` then it should be a string
        }
        seeder = left==0
        peer = Peer(info_hash=info_hash,
                    peer_id=peer_id,
                    port=port,
                    uploaded=uploaded,
                    downloaded=downloaded,
                    event=event,
                    agent=torrent_client.get("family"),
                    seeder=seeder, **ip.todict()
                )
        peers = PeerList(seeder=seeder, info_hash=info_hash, requester_ip=ip, compact=(compact == 1))
        rep_dict.update(peers())
        rep_dict.update(get_peer_count(info_hash))
        if event == 'stopped':
            peer.commit(next_allowance = timedelta(seconds=0), seeder=seeder)
        else:
            peer.commit(seeder=seeder)
        return BencResponse(rep_dict)
    except ErrorException as e:
        return ErrorResponse(e.__repr__())


@gg.get('/scrape')
async def scrape(
    request:Request,
    info_hash: bytes,
    passkey: str
):
    rep_dict = {
        "files": get_peer_count(info_hash)
    }
    return BencResponse(rep_dict)
