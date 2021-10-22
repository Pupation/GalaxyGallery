import bencodepy
from typing import Tuple, Union, BinaryIO, List
from hashlib import sha1
from .size_parser import parse_size

class Torrent:
    def __init__(self, content: Union[bytes, BinaryIO]):
        if not isinstance(content, bytes):
            content = content.read()
        self.torrent = bencodepy.decode(content)
        self.torrent[b'info'][b'private'] = 1 # by default, we set it as private

    def set_announce(self, url: Union[str, List[str]]):
        self.torrent[b'announce-list'] = []
        if isinstance(url, list):
            self.torrent[b'announce-list'] = url
            url = url[0]
        self.torrent[b'announce'] = url
    
    def get_torrent(self) -> bytes:
        return bencodepy.encode(self.torrent)
    
    def get_size(self, format_size=False) -> Union[int, Tuple[int, str]]:
        if b'length' in self.torrent[b'info']:
            ret = self.torrent[b'info'][b'length']
        else:
            ret = 0
            for file in self.torrent[b'info'][b'files']:
                ret += file[b'length']
        if format_size:
            return parse_size(ret)
        else:
            return ret
        
    def get_filelist(self) -> List[str]:
        if b'name' in self.torrent[b'info']:
            return [self.torrent[b'info'][b'name'].decode('utf-8')]
        else:
            ret = []
            for file in self.torrent[b'info'][b'files']:
                ret.append(file[b'name'].decode('utf-8'))
            return ret
    
    def get_info_hash(self) -> bytes:
        return sha1(bencodepy.encode(self.torrent[b'info'])).digest()

if __name__ == "__main__":
    import glob
    for filename in glob.glob('/Users/mingjun97/Downloads/*.torrent'):
        # print(filename)
        t = Torrent(open(filename, 'rb'))
        print(filename)
        print(t.torrent.keys())
        print(t.get_size())
        t.set_announce('http://localhost:8000/announce?passkey=helloworld')
        print(t.get_info_hash())

    