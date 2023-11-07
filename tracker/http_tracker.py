import bencode
import aiohttp

from urllib.parse import urlencode 
from hashlib import sha1

from .tracker import Tracker
from torrent import TorrentFile
from piece_manager import PieceManager

class HTTPTracker(Tracker):
    def __init__(self, torrent_file: TorrentFile, piece_manager: PieceManager):
        self.torrent       = torrent_file
        self.http_session  = aiohttp.ClientSession()
        self.piece_manager = piece_manager
        self.info_hash     = sha1(bencode.dumps(self.torrent.info)).digest()

    def _build_request(self, event: str) -> str:
        """ Returns the URL with all query params set for given torrent """
        params = {
            'info_hash':  self.info_hash,
            'peer_id':    'something1.0',
            'port':       59321,
            'downloaded': self.piece_manager.downloaded(),
            'uploaded':   self.piece_manager.uploaded(),
            'left':       self.piece_manager.total_piece_nr() - self.piece_manager.downloaded(),
            'compact':    1,
            'event':      event,
            'numwant':    30
        }

        return self.announce + "?" + urlencode(params)
    
    async def get_peers(self):
        async with self.http_session.get(self._build_request()) as resp:
            if resp.status != 200:
                return

            response = bencode.loads(await resp.read())
        
        return response
        



