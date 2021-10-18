from fastapi import Header, Request
from datetime import timedelta

from main import gg
from utils.response import BencResponse, ErrorResponse
from utils.checker import check_ip, check_ua_or_400, check_port_or_400
from models.helper import ErrorException
from models.torrent import Peer, PeerList

getPeers = PeerList()

@gg.get('/announce')
async def announce(
    request: Request,

    port: int, passkey: str, info_hash: bytes,
    peer_id: str, key: str, uploaded: int, downloaded: int, left: int,
    compact: int = 0, no_peer_id: int = 0,
    event: str = '',
    supportcrypto: bool = False, requirecrypto: bool = False,
    ipv6: str = '',

    user_agent: str = Header(None)
):
    if event not in ['started', 'completed', 'stopped', 'paused', '']:
        return ErrorResponse('Unknown event.')
    # print(info_hash, peer_id)
    ip = request.client.host # FIXME: get ip
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
            "complete": 20,
            "incomplete": 10
            # "peers" : None  # By default it is a array object, only when `&compact=1` then it should be a string
        }
        seeder = left==0
        peer = Peer(info_hash=info_hash, peer_id=peer_id,ipv4=request.client.host, ipv6=ipv6, port=port, uploaded=uploaded, downloaded=downloaded, event=event,agent=torrent_client.get("family"),seeder=seeder)
        if compact == 1:  # FIXME: not tested yet
            if ipv6 != '':
                rep_dict['peers6'] = getPeers(seeder=seeder, info_hash=info_hash, ip_version=6, requester_ip = ipv6, compact=True)
            else:
                rep_dict['peers'] = getPeers(seeder=seeder, info_hash=info_hash, ip_version=4, requester_ip=ip, compact=True)
        else:
            rep_dict['peers'] = getPeers(seeder=seeder, info_hash=info_hash, ip_version=6, requester_ip=ipv6, compact=False)
        if event == 'stopped':
            peer.commit(next_allowance = timedelta(seconds=0), seeder=seeder)
        else:
            peer.commit(seeder=seeder)
        return BencResponse(rep_dict)
    except ErrorException as e:
        return ErrorResponse(e.__repr__())


@gg.get('/scrape')
async def scrape():
    rep_dict = {
        "files": {
            "complete": 0,
            "downloaded": 1,
            "incomplete": 10
        }
    }
    return BencResponse(rep_dict)
