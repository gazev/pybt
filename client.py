from binascii import hexlify
from os import urandom

class Client:
    """ Class that keeps all our configuration options """
    def __init__(self, port: int):
        self.port = port
        self.id = "-ZZ0001-" + hexlify(urandom(6)).decode("utf-8") 

