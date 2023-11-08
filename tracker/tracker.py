from typing import Protocol, List

class PeerResponse:
    def __init__(self, ip: str, port: int):
        self.ip   = ip
        self.port = port


class Tracker(Protocol):
    async def get_peers(self) -> List[PeerResponse]:
        """ Returns a list of peers """
        raise NotImplementedError

