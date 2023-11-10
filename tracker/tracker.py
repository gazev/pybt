from typing import Protocol, Tuple, List

from dataclasses import dataclass

@dataclass(frozen=True)
class PeerResponse:
    """ Class that represents information of a peer retrieved from the tracker """
    ip:   str 
    port: int


class Tracker(Protocol):
    async def get_peers(self) -> Tuple[List[PeerResponse], int]:
        """ This is a function that will be called periodically to retrieve peers

        It will also return the Interval time it is expected for a client to wait 
        before another request is made
         """
        raise NotImplementedError
    
    async def close(self) -> None:
        """ Perform all logic to end communication with Tracker """
        raise NotImplementedError

