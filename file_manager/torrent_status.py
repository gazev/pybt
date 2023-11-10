from typing import Protocol

class TorrentStatus(Protocol):
    """ Class used to keep track of current Torrent status """
    def get_uploaded(self) -> int:
        raise NotImplementedError

    def get_downloaded(self) -> int:
        raise NotImplementedError
    
    def get_total_pieces_nr(self) -> int:
        raise NotImplementedError

