from typing import Protocol, Any, List
from enum import Enum
from math import ceil

from peer import Peer
import bitarray

class PieceState(Enum):
    MISSING = 0
    PENDING = 1
    COMPLETE = 2

class TorrentManager:
    def __init__(self, meta_info: InfoDict):
        self._meta_info    = meta_info
        self._file_manager = SingleFileManager(meta_info)
        self._pieces_state = bitarray(
            math.ceil(meta_info['lenght'] / meta_info['piece length'])
        )

    def get_pieces(self, amount: int, bitfield: bitarray.bitarray) -> List[int]:

        pass

