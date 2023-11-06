CACHE_SIZE = 50 

from typing import Protocol, Dict
from cache import lru_cache

from buffer import PiecesWriteBuffer

class PieceManager(Protocol):
    """ A class that performs the managment of the pieces in a torrent, such as,
    writting/reading data, selecting piece requests, etc.
    """
    def read_piece(self, index: int) -> bytes:
        raise NotImplementedError

    def write_piece(self, index: int, piece: bytes) -> None:
        raise NotImplementedError
    
    def next_desired_piece(self) -> int:
        raise NotImplementedError
    
    def update_state(self, update: int | List[bool]) -> None:
        raise NotImplementedError


class FilePieceManager(PieceManager): 
    def __init__(self, torrent_info, piece_sel_strategy: PieceSelectionStrategy):
        self.file       = file_path 
        self.piece_size = piece_size
        self.strategy   = strategy_sel_strategy

        self.buffer : PiecesWriteBuffer() 


    @property
    def piece_sel_strategy(self):
        return self._strategy


    @piece_strategy.setter
    def piece_sel_strategy(self, strategy: PieceSelectionStrategy):
        strategy.initialize(piece_size)

        self._strategy = strategy 


    @lru_cache(cache_size=CACHE_SIZE)
    def read_piece(self, index: int) -> bytes:
        with open(self.file, 'rb') as fp:
            fp.seek(index * self.piece_size, 0)
            return fp.read(self.piece_size)


    def write_piece(self, index: int, piece: bytes) -> None:
        if self.buffer.is_full():
            self.buffer.flush()
        
        self.buffer.add(index, piece)
    

    def next_desired_piece(self):
        self.strategy.get_next_piece()
    

    def update_state(self, update: int | List[bool]):
        if isinstance(update, int):
            self.strategy.update_new_piece()
        else:
            self.strategy.update_new_bitfield()

        

p = FilePieceManager("../test.txt", 1)


import time
import random

s = time.time()
# for _ in range(1000):
for i in range(100000):
    p.read_piece(random.randint(1,40))

print(time.time() - s)