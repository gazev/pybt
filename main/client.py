from binascii import hexlify
from os import urandom

class Client:
    """
    Class that keeps all our configuration options
    """
    def __init__(self, max_peers: int, port: int):
        self.port = port
        self.max_peers = max_peers
        self.id = "-VU0001-" + hexlify(urandom(6)).decode("utf-8") 

