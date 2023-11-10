import struct

from enum import Enum

#--------------------****------------------#
#                  Constants               #
#--------------------****------------------#
class Message(Enum):
    """" IDs of the protocol messages """
    CHOKE = 0
    UNCHOKE = 1
    INTERESTED = 2
    NOT_INTERESTED = 3
    HAVE = 4
    BITFIELD = 5
    REQUEST = 6 
    PIECE = 7
    CANCEL = 8

class FormatStrings(Enum):
    """ Strings that represent the binary data of messages of the protocol used
    for struct.pack and struct.unpack
    
    Example for Handshake: 
        - > | < identifies endianness, big | little respectively
        - B = 1 byte (indicating length of following string)
        - 19s = 19 bytes string
        - 8x = 8 pad bytes
        - 20s - 20 byte string (always 20, because it's the info hash)
        - 20s - 20 byte string (always 20, because it s the client id)
        """
    HANDSHAKE = '>B19s8x20s20s'
    CHOKE = '>I'
    UNCHOKE = '>I'
    INTERESTED = '>IB'
    NOT_INTERESTED = '>IB'
    REQUEST = '>IBIII'
    CANCEL = '>IBII'

#--------------------****------------------#
#                  Messages                #
#--------------------****------------------#
class Handshake:
    def __new__(self, client_id: str, info_hash: bytes) -> bytes:
        return struct.pack(FormatStrings.HANDSHAKE, 19, b'BitTorrent protocol', info_hash, client_id.encode())


class Choke:
    def __new__(self) -> bytes:
        return struct.pack('>I', 1, CHOKE)


class Unchoke:
    def __new__(self) -> bytes:
        return struct.pack('>I', 1, UNCHOKE)


class Interested:
    def __new__(self) -> bytes:
        return struct.pack('>IB', 1, INTERESTED)


class NotInterested:
    def __new__(self) -> bytes:
        return struct.pack('>IB', 1, NOT_INTERESTED)


class Request:
    def __new__(self, index: int, offset: int) -> bytes:
        return struct.pack('>IBIII', 13, REQUEST, index, offset * BLOCK_SIZE, BLOCK_SIZE)

class Cancel:
    def __new__(self, index: int, offset: int) -> bytes:
        return struct.pack('>IBIII', 13, CANCEL, index, offset * size, BLOCK_SIZE)
