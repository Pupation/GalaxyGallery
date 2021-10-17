from fastapi import Header, Request


from main import gg
from utils.response import BencResponse, ErrorResponse
from utils.checker import check_ip, check_ua_or_400, check_port_or_400
from models.helper import ErrorException
from models.torrent import Peer


# FIXME: For testing purposes only
p = Peer(**{
    'torrent': 0,
    'seeder': True,
    'peer_id': b'aaa',
    'ipv6': '2001::1' ,
    'port': 25678,
    'started': '2021-10-21 21:00:21',
    'last_action': '2021-10-21 21:00:21',
    'prev_action': '2021-10-21 21:00:21',
    'userid': 0,
    'agent': b'111',
    'passkey': '123'
})

@gg.get('/announce')
async def announce(
    request: Request,

    port:int, passkey:str, info_hash:bytes,
    peer_id:str, key:str, uploaded: int, downloaded: int, left:int,
    compact: int = 0, no_peer_id:int=0,
    event:str='',
    supportcrypto:bool = False, requirecrypto:bool = False,
    ipv6:str = '',

    user_agent: str = Header(None)
):
    if event not in ['started', 'completed', 'stopped', 'paused', '']:
        return ErrorResponse('Unknown event.')
    # print(info_hash, peer_id)
    ip = '0.0.0.0' # FIXME: get ip 
    # print(request.headers)
    # FIXME: BEAWARE DoS! Blocked ip address still able to consume server computation resource
    try:

        coroutine_checkip = check_ip(ip)

        client = check_ua_or_400(request)
        check_port_or_400(port)
        blocked_ip = await coroutine_checkip
        if blocked_ip:
            raise ErrorException('Blocked IP.')

        rep_dict = {
            "interval": 15,
            "min interval":  10,
            "complete" : 20,
            "incomplete" : 10
            # "peers" : None  # By default it is a array object, only when `&compact=1` then it should be a string
        }
        
        if compact: # FIXME: not tested yet
            if ipv6:
                rep_dict['peers6'] = p(True, 6)
            else:
                rep_dict['peers'] = p(True, 6)
        else:
            rep_dict['peers'] = p(False, 6)
        return BencResponse(rep_dict)
    except ErrorException as e:
        return ErrorResponse(e.__repr__())

@gg.get('/scrape')
async def scrape():
    rep_dict = { 
        "files":{
            "complete": 0,
            "downloaded" : 0,
            "incomplete" : 0
            }
        }
    return BencResponse(rep_dict)