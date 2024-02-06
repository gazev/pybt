from __future__ import annotations

from typing import Dict, Any


import math
import bencode

from hashlib import sha1
from functools import cached_property

class BadTorrent(KeyError):
    """ If we don't have enough information to continue with our version of the
    protocol
    """
    ...

class InfoDict:
    __required_keys = {
        'name', 'length', 'piece length', 'pieces'
    }

    def __init__(self, **kwargs):
        if self.__required_keys - set(kwargs.keys()):
            raise BadTorrent(f"Missing keys: {self.__required_keys - set(kwargs.keys())}")

        if not isinstance(kwargs['name'], bytes):
            raise BadTorrent('Name is not a string')

        if not isinstance(kwargs['length'], int):
            raise BadTorrent('Length is not an int')

        if not isinstance(kwargs['piece length'], int):
            raise BadTorrent('Piece length is not an int')

        if not isinstance(kwargs['pieces'], bytes):
            raise BadTorrent('Pieces key is not a byte string')

        self._inner_dict = kwargs
    

    @cached_property
    def total_pieces(self) -> int:
        return math.ceil(self['length'] / self['piece length'])
    

    def get_hash(self, n: int) -> bytes:
        return self['pieces'][20 * n: 20 * n + 20]


    def __getitem__(self, key):
        if key in self._inner_dict:
            return self._inner_dict[key]
        
        return None
        

class TorrentFile:
    __required_keys = {
        'announce', 'info'
    }

    @staticmethod
    def from_file(path: str) -> TorrentFile:
        with open(path, 'rb') as fp:
            return TorrentFile(**bencode.load(fp))


    def __init__(self, **kwargs):
        if self.__required_keys - set(kwargs.keys()):
            raise BadTorrent(f'Missing keys: {self.__required_keys - set(kwargs.keys())}')

        if not isinstance(kwargs['announce'], bytes):
            raise BadTorrent('Announce is not a string')

        if not isinstance(kwargs['info'], dict):
            raise BadTorrent('Info is not a dictionary')
        

        self._info_hash = sha1(bencode.dumps(kwargs['info'])).digest()
        self._inner_dict = kwargs
        self._inner_dict['info'] = InfoDict(**kwargs['info'])


    @property
    def info_hash(self):
        return self._info_hash


    def __getitem__(self, key: str) -> Any:
        if key in self._inner_dict:
            return self._inner_dict[key]
        
        return None
    
