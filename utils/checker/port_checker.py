from main import config
from models.helper import ErrorException

def check_port_or_400(port_number):
    if port_number < 1024 or \
        port_number > 0xffff or \
        port_number in config.client.banned_ports:
        raise ErrorException("Your are not allowed to use this port. %d" % port_number)