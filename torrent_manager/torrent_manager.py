from __future__ import annotations

from typing import TYPE_CHECKING

import math

from typing import Protocol, Any, List
from enum import Enum

import bitarray

from file_manager.single_file_manager import SingleFileManager 

if TYPE_CHECKING:
    from peer import Peer

class PieceState(Enum):
    MISSING = 0
    PENDING = 1
    COMPLETE = 2

class TorrentManager:
    def __init__(self, meta_info: InfoDict):
        self._meta_info    = meta_info
        self._file_manager = SingleFileManager(meta_info)
        self._pieces_state = \
            [PieceState.MISSING]* math.ceil(meta_info['length'] / meta_info['piece length'])
        
        self._first_missing_idx = 0

    def get_pieces(self, bitfield: bitarray.bitarray) -> int | None:
        """ Get pieces to request to a peer """
        for idx, val in enumerate(self._pieces_state, start=self._first_missing_idx):
            if bitfield[idx] and val == PieceState.MISSING:
                self._pieces_state[idx] = PieceState.PENDING
                return idx
           
        return None 
    
    def put_pieces(self, n: int):
        """ Enqueue back pieces that couldn't be retrieved """
        self._pieces_state[n] = PieceState.MISSING



