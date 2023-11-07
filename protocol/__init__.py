import struct

from config import BOCK_SIZE

CHOKE = 0
UNCHOKE = 1
INTERESTED = 2
NOT_INTERESTED = 3
HAVE = 4
BITFIELD = 5
REQUEST = 6 
PIECE = 7
CANCEL = 8


class Handshake:
    def __new__(self, client_id: str, info_hash: bytes):
        return struct.pack('>B19s8x20s20s', 19, b'BitTorrent protocol', info_hash, client_id.encode())


class KeepAlive:
    def __new__(self):
        return struct.pack('>I', 0)


class Choke:
    def __new__(self):
        return struct.pack('>I', 1, CHOKE)


class Unchoke:
    def __new__(self):
        return struct.pack('>I', 1, UNCHOKE)


class Interested:
    def __new__(self):
        return struct.pack('>IB', 1, INTERESTED)


class NotInterested:
    def __new__(self):
        return struct.pack('>IB', 1, NOT_INTERESTED)


class Request:
    def __new__(self, index: int, offset: int):
        return struct.pack('>IBIII', 13, REQUEST, index, offset * BLOCK_SIZE, BLOCK_SIZE)

class Cancel:
    def __new__(self, index: int, offset: int):
        return struct.pack('>IBIII', 13, CANCEL, index, offset * size, BLOCK_SIZE)