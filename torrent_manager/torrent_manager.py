from typing import Protocol, Any

class TorrentManager(Protocol):
    def register_peer(self, peer):
        raise NotImplementedError
    
    def unregister_peer(self, peer):
        raise NotImplementedError

    def get_rarest_piece(data: Any) -> int:
        """ Get rarest piece, used by peers. data arg can be used for 
        calculations, such as, to check if peer has piece """
        raise NotImplementedError


