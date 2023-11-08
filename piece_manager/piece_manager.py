from typing import Protocol, List

class PieceManager(Protocol):
    """ 
    A class that performs the managment of the pieces in a torrent, such as,
    writting/reading data, selecting piece requests, etc.
    """
    def read_piece(self, index: int) -> bytes:
        raise NotImplementedError

    def write_piece(self, index: int, piece: bytes) -> None:
        raise NotImplementedError
    
    def next_desired_piece(self) -> int:
        raise NotImplementedError
    
    def update(self, update: int | List[bool]) -> None:
        raise NotImplementedError
