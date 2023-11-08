from typing import Protocol

class TorrentStatus(Protocol):
    """ 
    Class used to keep track of current Torrent status, usually also implemented
    by PieceManager but not necessarily
     """
    def get_uploaded(self) -> int:
        raise NotImplementedError

    def get_downloaded(self) -> int:
        raise NotImplementedError
    
    def get_total_piece_nr(self) -> int:
        raise NotImplementedError

