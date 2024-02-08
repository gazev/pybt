from typing import List, Tuple

import bencode
import aiohttp
from urllib.parse import urlencode 
from hashlib import sha1
from ipaddress import ip_address
from struct import unpack


from client import Client

from tracker import (
    Tracker, 
    PeerAddr
)

from file_manager import (
    FileManager, 
    TorrentStatus
)

from torrent import TorrentFile

from .http_tracker_response import InvalidResponseException

from .http_tracker_exceptions import (
    HTTPTrackerException,
    DeadTrackerException, 
    RequestRejectedException,
    BadResponseException,
    GeneralException
)

from .http_tracker_response import HTTPTrackerResponse

from .utils import peer_lst_f_raw_str

class HTTPTracker(Tracker):
    def __init__(self, client: Client, torrent: TorrentFile):
        self._client         = client
        self._torrent        = torrent
        self._http_session   = aiohttp.ClientSession()
        # self._torrent_status = torrent_status 
        self._event_state    = 'started'
    

    async def get_peers(self) -> Tuple[List[PeerAddr], int]:
        try:
            raw_response = await self._request_tracker()
        except HTTPTrackerException:
            # TODO implement multi announce logic
            raise

        try:
            tracker_response = HTTPTrackerResponse(**bencode.loads(raw_response))
        except (bencode.BencodeDecodingError, InvalidResponseException) as e:
            raise HTTPTrackerException

        if tracker_response['failure reason']:
            self._handle_failure(tracker_response['failure reason'])
            return None, 10 

        return peer_lst_f_raw_str(tracker_response['peers']), tracker_response['interval']


    async def close(self) -> None:
        try:
            resp = await self._http_session.get(self._build_request('stopped'))
        except Exception as e:
            # at this point we don't care if we fail
            print(str(e), flush=True)
        
        await self._http_session.close()
        
        return


    async def _request_tracker(self) -> str:
        """ Make a GET request to the Tracker and return the raw content """
        try:
            async with self._http_session.get(self._build_request(self._event_state)) as resp:
                if resp.status != 200:
                    raise RequestRejectedException(f"Tracker didn't accept our request, status: {resp.status}") 
                
                return await resp.read()

        except aiohttp.ClientConnectionError as e:
            raise DeadTrackerException(e.host)
        except Exception as e:
            raise GeneralException(e)


    def _build_request(self, event: str) -> str:
        """ Build GET request to Tracker with specified event """
        params = {
            'info_hash':  self._torrent.info_hash,
            'peer_id':    self._client.id,
            'port':       self._client.port,
            # 'downloaded': self._torrent_status.get_downloaded(),
            # 'uploaded':   self._torrent_status.get_uploaded(),
            # 'left':       self._torrent_status.get_total_pieces_nr() - self._torrent_status.get_downloaded(),
            'compact':    1,
            'event':      event,
            # 'numwant':    self._client.max_peers * 2
            'numwant':    100 
        }

        return self._torrent['announce'].decode('utf-8') + '?' + urlencode(params)

    def _handle_failure(self, failure_reason: str):
        raise NotImplementedError
