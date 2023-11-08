from typing import Protocol, List, Tuple


class PeerResponse:
    def __init__(self, ip: str, port: int):
        self.ip   = ip
        self.port = port


class Tracker(Protocol):
    async def get_peers(self) -> List[PeerResponse]:
        """ Returns a list of peers (tuple with IP str and port int) """
        raise NotImplementedError


