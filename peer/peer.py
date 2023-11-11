from typing import Tuple

import asyncio
import struct

from torrent import TorrentFile
from client import Client
from tracker import PeerResponse

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

from .peer_exceptions import (
    PeerConnectionError,
    PeerConnectionOpenError,
    PeerConnectionReadError,
    PeerConnectionHandshakeError
)


class Peer:
    def __init__(self, peer_response: PeerResponse, torrent: TorrentFile, client: Client):
        self.ip    = peer_response.ip
        self.port  = peer_response.port 
        self.state = 'choked'

        self.torrent = torrent
        self.client  = client

        self.conn = PeerConnection(self)
    

    async def run(self):
        """ Peer event loop """
        try:
            await self.conn.initialize()
            # iterator returns message op code and payload
            async for op_code, message in PeerMessageStream(self.conn):
                print(f"Message from peer {self.ip}:{self.port}")
                print(op_code)
        
        except PeerConnectionError as e:
            print(str(e))
            raise
    
    async def end(self):
        await self.conn.close()


class PeerConnection:
    """ Wrapper to asyncio.reader and writer wrappers """
    def __init__(self, ctx: Peer):
        self._ctx = ctx
        self._reader = None
        self._writer = None


    async def initialize(self) -> None:
        """ Open connectino to peer and complete handshake.

        Raises a PeerConnectionError if not unsuccessful 
        """
        self._reader, self._writer = await self._open_conn()

        await self._send(Handshake(self._ctx.client.id, self._ctx.torrent.info_hash))

        response = await self._recv(struct.calcsize(FormatStrings.HANDSHAKE))

        if response[28:48] != self._ctx.torrent.info_hash:
            raise PeerConnectionHandshakeError(f'Bad handshake from peer {self._ctx.ip}:{self._ctx.port}') 

    async def close(self):
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()

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
            raise PeerConnectionOpenError(repr(e))
        
        return reader, writer 
    

    async def _send(self, msg):
        self._writer.write(msg)
        await self._writer.drain()
    
        
    async def _recv(self, size):
        # TO DO, i believe this should timeout if we are not receiving messages
        #  for some time since keep-alive messages should be expected 
        read_task = self._reader.read(size)

        try:
            data = await asyncio.wait_for(read_task, timeout=5.0)
        except TimeoutError:
            raise PeerConnectionReadError(f'Timed out peer {self._ctx.ip}:{self._ctx.port}')
        except ConnectionResetError:
            raise PeerConnectionReadError(f'Connection closed from peer {self._ctx.ip}:{self._ctx.port}')
        except Exception as e:
            raise PeerConnectionReadError(repr(e))
        
        return data 


class PeerMessageStream:
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

