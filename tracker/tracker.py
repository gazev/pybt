from typing import Protocol, Tuple, List

class PeerResponse:
    def __init__(self, ip: str, port: int):
        self.ip   = ip
        self.port = port


class Tracker(Protocol):
    async def get_peers(self) -> Tuple[List[PeerResponse], int]:
        """ 
        This is a function that will be called periodically to retrieve peers
        It will also return the Interval time it is expected for a client to wait 
        before another request is made
         """
        raise NotImplementedError

