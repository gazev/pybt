from torrent import TorrentFile
from math import ceil

class TorrentStatus:
    def __init__(self, torrent: TorrentFile):
        self._downloaded: int = 0
        self._uploaded:   int = 0
        self._total_pieces_nr: int = \
            ceil((torrent['info']['length'] / torrent['info']['piece length']))
            # round up the value because last piece might not fill the entire space 


    def get_downloaded(self) -> int:
        return self._downloaded
    

    def get_uploaded(self) -> int:
        return self._uploaded
    

    def get_total_pieces_nr(self) -> int:
        return self._total_pieces_nr

