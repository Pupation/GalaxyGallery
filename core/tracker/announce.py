from main import gg

from utils.response import BencResponse, ErrorResponse

from utils.checker.ip_checker import check_ip

from time import sleep

@gg.get('/announce')
async def announce(
    passkey:str='', info_hash:bytes='', peer_id:str='',
    event:str='', key:str='',
    
    port:int =0,uploaded: int = 0, downloaded: int=0,
    left:int = 0, compact: int = 0, no_peer_id:int=0,

    supportcrypto:bool = False, requirecrypto:bool = False,
    ipv6:str = ''
):
    if event not in ['started', 'completed', 'stopped', 'paused', '']:
        return ErrorResponse('Unknown event.')
    # print(info_hash, peer_id)
    ip = '0.0.0.0' # FIXME: get ip 

    # FIXME: BEAWARE DoS! Blocked ip address still able to consume server computation resource
    coroutine_checkip = check_ip(ip)


    blocked_ip = await coroutine_checkip

    if blocked_ip:
        return ErrorResponse('Blocked IP.')

    rep_dict = {
        "interval": "1",
        "min interval":  "1",
        "complete" : '20',
        "incomplete" : '10',
        "peers" : [123,['442']]  # By default it is a array object, only when `&compact=1` then it should be a string
    }
    return BencResponse(rep_dict)