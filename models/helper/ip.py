from typing import Optional

class IP:
    ipv4: Optional[str]
    ipv6: Optional[str]

    def __init__(self, client_host=None, ipv6=None):
        if client_host == '' or (client_host is not None and ':' in client_host):
            self.ipv4 = None 
            self.ipv6 = client_host
            return
        else:
            self.ipv4 = client_host

        if ipv6 == '':
            self.ipv6 = None
        else:
            self.ipv6 = ipv6

    def todict(self):
        ret = dict()
        if self.ipv4 is not None:
            ret['ipv4'] = self.ipv4
        if self.ipv6 is not None:
            ret['ipv6'] = self.ipv6
        return ret

    def __repr__(self):
        ret = []
        if self.ipv4 is not None:
            ret.append("IPv4=" + self.ipv4)
        if self.ipv6 is not None:
            ret.append("IPv6=" + self.ipv6)
        return f"IP({','.join(ret)})"
    
    def has_ipv4(self):
        return self.ipv4 is not None
    
    def has_ipv6(self):
        return self.ipv6 is not None

    def has(self):
        return self.has_ipv4() or self.has_ipv6()

        
        
if __name__ == '__main__':
    print(IP('10.0.0.1','2001::1'))
    print(IP('10.0.0.1'))
    print(IP('2001::1'))
    print(IP())
    print(IP(ipv6="2001::1"))
    print('ipv4' in IP('10.0.0.1').todict())
    print('ipv6' in IP('10.0.0.1').todict())