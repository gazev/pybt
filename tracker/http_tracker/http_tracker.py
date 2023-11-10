from typing import List

import bencode
import aiohttp
from urllib.parse import urlencode 
from hashlib import sha1
from ipaddress import ip_address
from struct import unpack


from client import Client

from tracker import (
    Tracker, 
    PeerResponse
)

from file_manager import (
    FileManager, 
    TorrentStatus
)

from torrent import TorrentFile

from .http_tracker_exceptions import HTTPTrackerException

from .http_tracker_exceptions import (
    DeadTrackerException, 
    RequestRejectedException,
    BadResponseException,
    GeneralException
)

from .http_tracker_response import HTTPTrackerResponse

from .utils import peer_response_list_from_raw_str

class HTTPTracker(Tracker):
    _state = None

    def __init__(self, client: Client, torrent: TorrentFile, torrent_status: TorrentStatus):
        self._client         = client
        self._torrent        = torrent
        self._http_session   = aiohttp.ClientSession()
        self._torrent_status = torrent_status 
        self._info_hash      = sha1(bencode.dumps(self._torrent.info.to_dict())).digest()
        self._event_state    = 'started'
    

    async def get_peers(self) -> List[PeerResponse]:
        # NOTE Ideally we would keep a tracker state that would act accordingly to the
        # Tracker feedback (failure/warning messages and trackers not working), 
        # but since it's not clear what messages are mostly used we just make the 

        try:
            response: HTTPTrackerResponse = await self._request_tracker()
        except HTTPTrackerException:
            # TODO implement multi announce logic
            raise # since it's not done yet we just do this lol

        # see note on top of func definition
        if response.failure_reason:
            return []

        return peer_response_list_from_raw_str(response.peers), response.interval


    async def close(self) -> None:
        try:
            resp = await self._http_session.get(self._build_request('stopped'))
        except Exception as e:
            # at this point we don't care if we fail
            print(repr(e), flush=True)
        
        await self._close_session()
        
        return


    async def _close_session(self) -> None:
        await self._http_session.close()


    async def _request_tracker(self) -> HTTPTrackerResponse:
        # yes all this try-catch, can't be worse than if err != nil right?

        try:
            async with self._http_session.get(self._build_request(self._event_state)) as resp:
                if resp.status != 200:
                    return RequestRejectedException(f"Tracker didn't accept our request, status: {resp.status}") 

                try:
                    bencode_resp = bencode.loads(await resp.read())
                except bencode.BencodeDecodingError:
                    raise BadResponseException(f"Tracker didn't respond in Bencode format")

                try:
                    tracker_response = HTTPTrackerResponse(**bencode_resp)
                except http_tracker_response.InvalidResponseException as e:
                    raise BadResponseException(str(e))

                return tracker_response 

        except aiohttp.ClientConnectionError as e:
            raise DeadTrackerException(e.host)
        except Exception as e:
            raise GeneralException(e)


    def _build_request(self, event: str) -> str:
        """ Returns the URL with all query params set for given torrent """
        params = {
            'info_hash':  self._info_hash,
            'peer_id':    self._client.id,
            'port':       self._client.port,
            'downloaded': self._torrent_status.get_downloaded(),
            'uploaded':   self._torrent_status.get_uploaded(),
            'left':       self._torrent_status.get_total_pieces_nr() - self._torrent_status.get_downloaded(),
            'compact':    1,
            'event':      event,
            'numwant':    self._client.max_peers
        }

        return self._torrent['announce'].decode('utf-8') + '?' + urlencode(params)

