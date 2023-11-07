from typing import Protocol, Dict, List
from config import CACHE_SIZE, BUFFER_SIZE

from math import ceil

from torrent import TorrentFile
from .piece_selection_algorithm import PieceSelectionAlgorithm
from .piece_manager import PieceManager

from .cache import lru_cache
from .buffer import PiecesWriteBuffer


class FilePieceManager(PieceManager): 
    def __init__(self, torrent: TorrentFile, piece_sel_strategy: PieceSelectionAlgorithm):
        self.torrent  = torrent 
        self.buffer   = PiecesWriteBuffer(BUFFER_SIZE) 
        self.strategy = piece_sel_strategy

        self._downloaded:     int = 0
        self._uploaded:       int = 0
        self._total_piece_nr: int = \
            ceil((torrent.info['length'] / torrent.info['piece length'])) 
            # round up the value because last piece might not fill the entire space 

    def get_downloaded(self) -> int:
        return self._downloaded
    
    def get_uploaded(self) -> int:
        return self._uploaded
    
    def get_total_piece_nr(self) -> int:
        return self._total_piece_nr


    @property
    def piece_sel_strategy(self) -> PieceSelectionAlgorithm:
        return self._strategy


    @piece_sel_strategy.setter
    def piece_sel_strategy(self, strategy: PieceSelectionAlgorithm):
        strategy.initialize(piece_size)

        self._strategy = strategy 


    @lru_cache(cache_size=CACHE_SIZE)
    def read_piece(self, index: int) -> bytes:
        self._uploaded += 1

        if self.buffer.has_piece(index):
            return self.buffer.get_piece(index)

        with open(self.file, 'rb') as fp:
            fp.seek(index * self.piece_size, 0)
            return fp.read(self.piece_size)


    def write_piece(self, index: int, piece: bytes) -> None:
        self._downloaded += 1

        if self.buffer.is_full():
            self.buffer.flush()
        
        self.buffer.add(index, piece)
    

    def next_desired_piece(self):
        self.strategy.get_next_piece()
    

    def update(self, update: int | List[bool]):
        if isinstance(update, int):
            self.strategy.update_new_piece()
        else:
            self.strategy.update_new_bitfield()

        