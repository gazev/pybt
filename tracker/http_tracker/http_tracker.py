from typing import List

import bencode
import aiohttp
from urllib.parse import urlencode 
from hashlib import sha1
from ipaddress import ip_address
from struct import unpack


from tracker import (
    Tracker, 
    PeerResponse
)

from piece_manager import (
    PieceManager, 
    TorrentStatus
)


from torrent import TorrentFile


class HTTPTracker(Tracker):
    def __init__(self, torrent: TorrentFile, torrent_status: TorrentStatus):
        self._torrent        = torrent
        self._http_session   = aiohttp.ClientSession()
        self._torrent_status = torrent_status 
        self._info_hash      = sha1(bencode.dumps(self._torrent.info.to_dict())).digest()
        self._event_state    = 'started'
    

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


    def update_state(self, new_state: str) -> None:
        self._event_state = new_state


    async def close_session(self) -> None:
        await self._http_session.close()


    async def _request_tracker(self) -> dict | None:
        try:
            async with self._http_session.get(self._build_request('start')) as resp:
                if resp._status != 200:
                    return None

                return bencode.loads(await resp.read())
        except Exception as e:
            # TODO handle exceptions that indicate a dead/broken tracker
            return None


    def _build_request(self) -> str:
        """ Returns the URL with all query params set for given torrent """
        params = {
            'info_hash':  self._info_hash,
            'peer_id':    'something1.0',
            'port':       59321,
            'downloaded': self._status.get_downloaded(),
            'uploaded':   self._status.get_uploaded(),
            'left':       self._status.get_total_piece_nr() - self._status.get_downloaded(),
            'compact':    1,
            'event':      self._event_state,
            'numwant':    30
        }

        return self._torrent['announce'].decode('utf-8') + '?' + urlencode(params)


    def _decode_ip(self, data: bytes) -> str:
        return str(ip_address(data))
    

    def _decode_port(self, data: bytes) -> int:
        return unpack(">H", data)[0]   


