import asyncio
import struct

from torrent import TorrentFile
from client import Client

from .peer_exceptions import (
    PeerConnectionOpenError,
    PeerConnectionReadError
)

class Peer:
    def __init__(self, ip: str, port: int, torrent: TorrentFile, client: Client):
        self.ip   = ip
        self.port = port
        self.state = 'chocked'

        self.torrent = torrent
        self.client  = client

        self.conn = PeerConnection(self)


class PeerConnection:
    """ Wrapper to asyncio.reader and writer wrappers """
    def __init__(self, ctx: Peer):
        self._ctx = ctx
        self._reader = None
        self._writer = None

    async def initialize(self):
        """ Open connectino to peer and complete handshake """
        self._reader, self._writer = self._open_conn()

        await self._send(protocol.Handshake(self._ctx.client.id, self._ctx.torrent.info_hash))

        response = await self._recv(struct.calcsize)

        if response[28:48] != self._ctx.torrent.info_hash:
            raise PeerConnectionHandshakeError('Bad handshake from peer {self._ctx.ip}:{self._ctx.port}') 


    async def _open_conn(self):
        """ Opens connection to peer, returning StreamReader and StreamWritter instances """
        open_conn_task = asyncio.open_connection(host=self._ctx.ip, port=self._ctx.port)

        try:
            asyncio.wait_for(
                await asyncio.open_connection(host=self.ip, port=self.port),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            raise PeerConnectionOpenError('Timed out connecting to {self._ctx.ip}:{self._ctx.port}')
        except ConnectionRefusedError:
            raise PeerConnectionOpenError('Connection refused from {self._ctx.ip}:{self._ctx.port}')
        except Exception as e:
            raise PeerConnectionOpenError(repr(e))
        
        return await open_conn_task
    
    async def _send(self, msg):
        self.writer.write(msg)
        await self.writer.drain()
    
        
    async def _recv(self, size):
        # TO DO, i believe this should timeout if we are not receiving messages
        #  for some time since keep-alive messages should be expected 
        try:
            return await self.reader.read(size)
        except ConnectionResetError:
            raise PeerConnectionReadError('Connection closed from peer {self._ctx.ip}:{self._ctx.port}')
        except Exception as e:
            raise PeerConnectionReadError(repr(e))

