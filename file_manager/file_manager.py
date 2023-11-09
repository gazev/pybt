from typing import Protocol, List

from tracker import PeerResponse

class FileManager(Protocol):
    """ 
    The class that is responsible for reading and writting data to/from the desired
    files of a Torrent
    """
    def read_piece(self, index: int) -> bytes:
        raise NotImplementedError

    def write_piece(self, index: int, piece: bytes) -> None:
        raise NotImplementedError
    
    def end(self):
        """ Perform shutdown logic """
        raise NotImplementedError
    
