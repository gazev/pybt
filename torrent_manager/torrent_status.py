from torrent import InfoDict

class TorrentStatus:
    def __init__(self, meta_info: InfoDict):
        self._meta_info = meta_info
        self._downloaded = 0
        self._uploaded = 0

    @property
    def downloaded(self):
        return self._downloaded * self._meta_info['piece length']

    @property
    def uploaded(self):
        return self._uploaded * self._meta_info['piece length']

    @property
    def left(self):
        return (self._meta_info.total_pieces - self._downloaded) * self._meta_info['piece length']
    
