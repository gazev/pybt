from typing import TypedDict, List, NotRequired
import bencode

class BadTorrent(KeyError):
    """ 
    If we don't have enough information to continue with our version of the
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

        self.info = kwargs
    
    def __getitem__(self, key):
        if key in self.info:
            return self.info[key]
        
        return None
        

class TorrentFile:
    __required_keys = {
        'announce', 'info'
    }

    def __init__(self, **kwargs):
        if self.__required_keys - set(kwargs.keys()):
            raise BadTorrent(f"Missing keys: {self.__required_keys - set(kwargs.keys())}")

        if not isinstance(announce, str):
            raise BadTorrent('Announce is not a string')

        if not isinstance(info, dict):
            raise BadTorrent('Info is not a dictionary')

        self.info = kwargs
    
    def __getitem__(self, key):
        if key in self.info:
            return self.info[key]
        
        return None
 