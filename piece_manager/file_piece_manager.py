from typing import Protocol, Dict, List

from .cache import lru_cache
from .buffer import PiecesWriteBuffer
from .piece_selection_algorithm import PieceSelectionAlgorithm

from torrent import TorrentFile

class FilePieceManager(PieceManager): 
    def __init__(self, torrent: TorrentFile, piece_sel_strategy: PieceSelectionAlgorithm):
        self.torrent  = torrent 
        self.buffer   = PiecesWriteBuffer(torrent.info['piece length']) 
        self.strategy = piece_sel_strategy

        self._downloaded:     int = 0
        self._uploaded:       int = 0
        self._total_piece_nr: int = \
            int((torrent.info['length'] / torrent.info['piece length']) + 1)
            # round up the value because last piece might not fill the entire space 

    def get_downloaded(self):
        return self._downloaded
    
    def get_uploaded(self):
        return self._uploaded
    
    def get_total_piece_nr(self):
        return self._total_piece_nr


    @property
    def piece_sel_strategy(self):
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

        