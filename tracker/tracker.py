from typing import Protocol, List, Tuple

class Tracker(Protocol):
    async def get_peers(self) -> List[Tuple[str, int]]:
        """ Returns a list of peers (tuple with IP str and port int) """
        raise NotImplementedError


