import struct

from typing import Tuple

from enum import IntEnum 
from enum import StrEnum

#--------------------****------------------#
#                  Constants               #
#--------------------****------------------#
class MessageOP(IntEnum):
    """ OP codes of the protocol messages """
    CHOKE = 0
    UNCHOKE = 1
    INTERESTED = 2
    NOT_INTERESTED = 3
    HAVE = 4
    BITFIELD = 5
    REQUEST = 6 
    PIECE = 7
    CANCEL = 8
    KEEP_ALIVE = -1 # this is not part of the spec

class FormatStrings(StrEnum):
    """ Strings that represent the binary data of messages of the protocol used
    for struct.pack and struct.unpack

    Example for Handshake: 
        - > | < identifies endianness, big | little respectively
        - B = 1 byte (representing length of following string)
        - 19s = 19 bytes string
        - 8x = 8 pad bytes
        - 20s = 20 byte string (always 20, because it's the info hash)
        - 20s = 20 byte string (always 20, because it s the client id)
        - I = 4 byte int (not used in Handshake)
    """
    HANDSHAKE = '>B19s8x20s20s'
    CHOKE = '>I'
    UNCHOKE = '>I'
    INTERESTED = '>IB'
    NOT_INTERESTED = '>IB'
    HAVE = '>IBI'
    REQUEST = '>IBIII'
    CANCEL = '>IBII'

#--------------------****------------------#
#                  Messages                #
#--------------------****------------------#
class Handshake:
    def __new__(self, client_id: str, info_hash: bytes) -> bytes:
        return struct.pack(FormatStrings.HANDSHAKE, 19, b'BitTorrent protocol', info_hash, client_id.encode())
    
    @staticmethod
    def decode(payload) -> Tuple[str, str]:
        return payload[28:48], payload[48:68]


class Choke:
    def __new__(self) -> bytes:
        return struct.pack(FormatStrings.CHOKE, 1, MessageOP.CHOKE)
    

class Unchoke:
    def __new__(self) -> bytes:
        return struct.pack(FormatStrings.UNCHOKE, 1, MessageOP.UNCHOKE)


class Interested:
    def __new__(self) -> bytes:
        return struct.pack(FormatStrings.INTERESTED, 1, MessageOP.INTERESTED)


class NotInterested:
    def __new__(self) -> bytes:
        return struct.pack(FormatStrings.NOT_INTERESTED, 1, MessageOP.NOT_INTERESTED)


class Have:
    def __new__(self, n: int) -> bytes:
        return struct.pack(FormatStrings.HAVE, 5, MessageOP.HAVE, n)
    
    @staticmethod
    def decode(payload) -> int:
        return struct.unpack(">I", payload)[0]


class Request:
    def __new__(self, index: int, offset: int) -> bytes:
        return struct.pack(FormatStrings.REQUEST, 13, REQUEST, index, offset * BLOCK_SIZE, BLOCK_SIZE)


class Cancel:
    def __new__(self, index: int, offset: int) -> bytes:
        return struct.pack(FormatStrings.CANCEL, 13, CANCEL, index, offset * size, BLOCK_SIZE)
