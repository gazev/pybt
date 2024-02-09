from typing import Protocol, Dict, List

from math import ceil

from torrent import InfoDict 
from file_manager import FileManager

from .cache import lru_cache


class SingleFileManager(FileManager): 
    """ Manager for single file torrents

    Implementing multi file support will build on top of this. This class is a 
    temporary placeholder before full implementation
    """
    def __init__(self, meta_info: InfoDict):
        self._file: str       = meta_info['name']
        self._piece_size: int = meta_info['piece length']
        self._fp = open(self._file, 'wb')


    @lru_cache(cache_size=50)
    def read_piece(self, index: int) -> bytes:
        """ Read a piece at index passed as arg (wrapped with a LRU cache)"""
        self._fp.seek(index * self._piece_size, 0)
        return self._fp.read(self._piece_size)


    def write_piece(self, index: int, piece: bytes) -> None:
        """ Write piece passed as arg to index passed as arg """
        self._fp.seek(index * self._piece_size, 0)
        self._fp.write(piece)


    """ Terminate, writting buffer to disk """
    def end():
        self._fp.flush()
        self._fp.close()

        