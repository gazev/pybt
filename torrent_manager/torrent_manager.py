from __future__ import annotations

from typing import TYPE_CHECKING

import math
import asyncio

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
    def __init__(self, meta_info: InfoDict, file_manager: SingleFileManager):
        self._meta_info    = meta_info
        self._file_manager = file_manager 
        self._endgame = False

        self._total_pieces = math.ceil(meta_info['length'] / meta_info['piece length'])
        self._pieces_state = [PieceState.MISSING] * self._total_pieces 
        self._dl_pieces = 0
        
        self._first_missing_idx = 0
        self.end = asyncio.Event()


    def get_pieces(self, bitfield: bitarray.bitarray) -> int | None:
        """ Get pieces to request to a peer """
        for idx in range(self._first_missing_idx, self._total_pieces):
            if bitfield[idx]:
                if self._pieces_state[idx] == PieceState.MISSING:
                    self._pieces_state[idx] = PieceState.PENDING
                    if idx == 2511:
                        self._endgame = True
                        self._first_missing_idx = 0
                    return idx

                if self._endgame and self._pieces_state[idx] != PieceState.COMPLETE:
                    self._pieces_state[idx] = PieceState.PENDING
                    return idx

        # for idx, val in enumerate(self._pieces_state, start=self._first_missing_idx):
        #     if bitfield[idx] and val == PieceState.MISSING:
          
        return None 

    
    def put_pieces(self, n: int):
        """ Enqueue back pieces that couldn't be retrieved """
        self._pieces_state[n] = PieceState.MISSING
    

    def save_piece(self, piece_nr:int, piece: bytes):
        if self._pieces_state[piece_nr] != PieceState.PENDING:
            return

        self._file_manager.write_piece(piece_nr, piece)
        self._pieces_state[piece_nr] = PieceState.COMPLETE

        self._dl_pieces += 1
        # update window
        print(f"Got piece {piece_nr}")
        if not self._endgame and self._first_missing_idx == piece_nr:
            for idx in range(self._first_missing_idx, self._total_pieces):
                if self._pieces_state[idx] == PieceState.MISSING:
                    self._first_missing_idx = idx
                    break
        
        if self._dl_pieces == self._total_pieces:
            print("End")
            self.end.set()

