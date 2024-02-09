from __future__ import annotations

import asyncio
import struct
import bitarray
import math

from torrent import TorrentFile
from client import Client
from tracker import PeerAddr 
from torrent_manager import TorrentManager
from protocol import MessageOP, FormatStrings

from protocol import (
    Handshake,
    Choke,
    Unchoke,
    Interested,
    NotInterested,
    Request,
    Cancel
)

from .peer_state import PeerState, ChokedNotInterested 
from .peer_exceptions import (
    PeerConnectionError,
    PeerConnectionOpenError,
    PeerConnectionReadError,
    PeerConnectionHandshakeError
)


class Peer:
    def __init__(
        self, 
        address: PeerAddr, 
        torrent: TorrentFile, 
        client: Client, 
        torrent_manager: TorrentManager
    ):
        self.addr = address 
        self.bitfield = bitarray.bitarray(
            math.ceil(torrent['info']['length'] / torrent['info']['piece length'])
        )

        self.am_choking = 1
        self.is_interested = 0

        self.torrent = torrent 
        self.client  = client
        self.torrent_manager = torrent_manager 

        self._state = ChokedNotInterested(self)
        self._conn = PeerConnection(self)


    @classmethod
    def from_incoming_conn(
        cls, 
        peer: PeerAddr,
        torrent: TorrentFile, 
        client: Client, 
        torrent_manager: TorrentManager,
        reader: asyncio.StreamReader, 
        writer: asyncio.StreamWriter
    ):
        p = cls(peer, torrent, client, torrent_manager) 
        p._conn._reader = reader
        p._conn._writer = writer
        
        return p

    @property
    def ip(self):
        return self.addr.ip

    @property
    def port(self):
        return self.addr.port


    async def initialize(self):
        """ Open TCP connection to Peer and perform Handshake """
        await self._conn.initialize()
    

    async def handshake(self):
        """ Handshake peer """
        await self._conn._handshake()


    def change_state(self, new_state: PeerState):
        self._state = new_state 


    async def send_message(self, msg: bytes):
        await self._conn._send(msg)


    async def run(self):
        """ Peer event loop """
        print(f'Connected to peer {self.ip}:{self.port}')
        try:
            # iterator returns message op code and payload
            async for op_code, payload in PeerMessageStreamIter(self._conn):
                if self.torrent_manager.end.is_set():
                    # await asyncio.sleep(.1) # 
                    return

                await self._state.handle_message(op_code, payload)
                await self._state.do_work()
            
        
        except PeerConnectionError as e:
            raise
            
        except Exception as e:
            # TODO add debug logging
            print(repr(e))
            pass
    

    async def end(self):
        try:
            if self._state._scheduled_piece is not None:
                self.torrent_manager.put_pieces(self._state._scheduled_piece)
        except AttributeError:
            pass
        await self._conn.close()


    def __hash__(self):
        return self.addr.__hash__()
    

    def __eq__(self, obj):
        if not isinstance(obj, Peer) and not isinstance(obj, PeerAddr):
            return False
        
        return obj == self.addr


class PeerConnection:
    """ Wrapper to asyncio.reader and writer wrappers """
    def __init__(self, ctx: Peer):
        self._ctx = ctx
        self._reader = None
        self._writer = None


    async def initialize(self) -> None:
        """ Open connection to peer and complete handshake """
        self._reader, self._writer = await self._open_conn()
        await self._handshake()


    async def close(self):
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except:
                pass


    async def _open_conn(self):
        """ Opens connection to peer, returning StreamReader and StreamWritter instances """
        open_conn_task = asyncio.open_connection(host=self._ctx.ip, port=self._ctx.port)

        try:
            reader, writer = await asyncio.wait_for(
                open_conn_task,
                timeout=5.0
            ) 
        except asyncio.TimeoutError:
            raise PeerConnectionOpenError(f'Timed out connecting to {self._ctx.ip}:{self._ctx.port}')
        except ConnectionRefusedError:
            raise PeerConnectionOpenError(f'Connection refused from {self._ctx.ip}:{self._ctx.port}')
        except Exception as e:
            raise PeerConnectionOpenError(f'Failed connecting to peer {self._ctx.ip}:{ßelf._ctx.port}')
        
        return reader, writer 
    

    async def _handshake(self):
        await self._send(Handshake(self._ctx.client.id, self._ctx.torrent.info_hash))

        response = await self._recv(struct.calcsize(FormatStrings.HANDSHAKE))

        info_hash, client_id = Handshake.decode(response)
        if info_hash != self._ctx.torrent.info_hash:
            raise PeerConnectionHandshakeError(f'Bad handshake from peer {self._ctx.ip}:{self._ctx.port}') 
    

    async def _send(self, msg: str):
        """ Write to StreamWriter """
        self._writer.write(msg)
        await self._writer.drain()
    
        
    async def _recv(self, size: int):
        """ Read from stream """
        read_task = self._reader.read(size)

        try:
            data = await asyncio.wait_for(read_task, timeout=20.0)
        except TimeoutError:
            raise PeerConnectionReadError(f'Timed out peer {self._ctx.ip}:{self._ctx.port}')
        except ConnectionResetError:
            raise PeerConnectionReadError(f'Connection closed from peer {self._ctx.ip}:{self._ctx.port}')
        except Exception as e:
            raise PeerConnectionReadError(repr(e))
        
        return data 


class PeerMessageStreamIter:
    """ Asyncio.StreamReader Iterator """
    def __init__(self, ctx: PeerConnection):
        self._ctx = ctx


    def __aiter__(self):
        return self 


    async def __anext__(self) -> Tuple[int, bytes]:
        """ Returns the message code and payload """

        # first 4B in messages indicate the length of the message
        msg_length = await self._ctx._recv(struct.calcsize(">I"))

        # connection was closed    
        if msg_length == b'':
            raise StopAsyncIteration

        msg_length = struct.unpack('>I', msg_length)[0]

        # keep alive messages identified with <len = 0>
        if msg_length == 0:
            return MessageOP.KEEP_ALIVE, None

        # read entire message from stream
        message = b''
        while msg_length > 0:
            buff = await self._ctx._recv(msg_length)
            message += buff
            msg_length -= len(buff)
        
        op_code: int = message[0]
        payload: bytes = message[1:]

        return op_code, payload

