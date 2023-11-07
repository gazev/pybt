from typing import List

import bencode
import aiohttp

from urllib.parse import urlencode 
from hashlib import sha1
from ipaddress import ip_address
from struct import unpack

from torrent import TorrentFile
from piece_manager import PieceManager

from .tracker import Tracker
from .peer_response import PeerResponse

class HTTPTracker(Tracker):
    def __init__(self, torrent: TorrentFile, piece_manager: PieceManager):
        self.torrent       = torrent
        self.http_session  = aiohttp.ClientSession()
        self.piece_manager = piece_manager
        self.info_hash     = sha1(bencode.dumps(self.torrent.info.to_dict())).digest()
        self.event_state   = 'started'
    

    async def get_peers(self) -> List[PeerResponse]:
        response: dict = await self._request_tracker()

        if response is None:
            return []

        raw_response: bytes = response['peers']

        # DONT use list comprehension because it's cursesd 
        peers: List[PeerResponse] = []
        for i in range(0, len(raw_response), 6):
            peers.append(
                PeerResponse(
                    self._decode_ip(raw_response[i:i+4]), 
                    self._decode_port(raw_response[i+4:i+6])
                )
            )
        
        return peers


    async def close_session(self) -> None:
        await self.http_session.close()


    async def _request_tracker(self) -> dict | None:
        try:
            async with self.http_session.get(self._build_request('start')) as resp:
                if resp.status != 200:
                    return None

                return bencode.loads(await resp.read())
        except Exception as e:
            # TODO handle exceptions that indicate a dead/broken tracker
            return None


    def _build_request(self) -> str:
        """ Returns the URL with all query params set for given torrent """
        params = {
            'info_hash':  self.info_hash,
            'peer_id':    'something1.0',
            'port':       59321,
            'downloaded': self.piece_manager.get_downloaded(),
            'uploaded':   self.piece_manager.get_uploaded(),
            'left':       self.piece_manager.get_total_piece_nr() - self.piece_manager.get_downloaded(),
            'compact':    1,
            'event':      self.event_state,
            'numwant':    30
        }

        return self.torrent['announce'].decode('utf-8') + '?' + urlencode(params)


    def _update_state(self, new_state: str) -> None:
        self.event_state = new_state


    def _decode_ip(self, data: bytes) -> str:
        return str(ip_address(data))
    

    def _decode_port(self, data: bytes) -> int:
        return unpack(">H", data)[0]   


