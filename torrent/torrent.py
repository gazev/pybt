from __future__ import annotations

from typing import Dict, Any

import bencode

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
    

    def to_dict(self) -> Dict:
        return self._inner_dict
    

    def __getitem__(self, key):
        if key in self._inner_dict:
            return self._inner_dict[key]
        
        return None
        

class TorrentFile:
    __required_keys = {
        'announce', 'info'
    }

    def __init__(self, **kwargs):
        if self.__required_keys - set(kwargs.keys()):
            raise BadTorrent(f"Missing keys: {self.__required_keys - set(kwargs.keys())}")

        if not isinstance(kwargs['announce'], bytes):
            raise BadTorrent('Announce is not a string')

        if not isinstance(kwargs['info'], dict):
            raise BadTorrent('Info is not a dictionary')
        
        self._inner_dict = kwargs
        self.__dict__['info'] = InfoDict(**kwargs['info'])
    

    def __getitem__(self, key: str) -> Any:
        if key in self._inner_dict:
            return self._inner_dict[key]
        
        return None


    @staticmethod
    def from_file(path: str) -> TorrentFile:
        with open(path, 'rb') as fp:
            return TorrentFile(**bencode.load(fp))

