from typing import Protocol, Dict, List
from config import CACHE_SIZE, BUFFER_SIZE

from math import ceil

from torrent import InfoDict 
from piece_algorithms import PieceSelectionAlgorithm

from file_manager import FileManager, TorrentStatus
from .cache import lru_cache
from .buffer import FileWriteBuffer 


class SingleFileManager(FileManager, TorrentStatus): 
    """ Manager for single file torrents

    Implementing multi file support will build on top of this. This class is a 
    temporary placeholder before full implementation
    """
    def __init__(self, meta_info: InfoDict):
        self._file: str       = meta_info['name']
        self._piece_size: int = meta_info['piece length']
        self._fp = open(self._file, 'wb')

        self._buffer = FileWriteBuffer(BUFFER_SIZE, self._piece_size, self._fp) 


    @lru_cache(cache_size=CACHE_SIZE)
    def read_piece(self, index: int) -> bytes:
        """ Read a piece at index passed as arg (wrapped with a LRU cache)"""
        if self._buffer.has_piece(index):
            return self._buffer.get_piece(index)

        self._fp.seek(index * self._piece_size, 0)
        return self._fp.read(self._piece_size)


    def write_piece(self, index: int, piece: bytes) -> None:
        """ Write piece passed as arg to index passed as arg """
        self._fp.seek(index * self._piece_size, 0)
        self._fp.write(piece)
        # if self._buffer.is_full():
        #     self._buffer.flush()
        
        # self._buffer.add(index, piece)
    

        """ Terminate, writting buffer to disk """
        def end():
            self._fp.flush()

        