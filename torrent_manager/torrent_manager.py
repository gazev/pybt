from typing import Protocol, Any, List

from peer import Peer
import bitarray

# class TorrentManager(Protocol):
#     def register_peer(self, peer):
#         raise NotImplementedError
    
#     def unregister_peer(self, peer):
#         raise NotImplementedError

#     def get_peer_work(data: Any) -> int:
#         """ Get rarest piece, used by peers. data arg can be used for 
#         calculations, such as, to check if peer has piece """
#         raise NotImplementedError

class TorrentManager(Protocol):
    def __init__(self):
        self.registered_peers = {}

    def update_peer(self, peer: Peer, payload):
        # self.register_peer.add[PeerTuple(peer.ip, peer.port)]
        pass

    def register_peer(self, peer: Peer, payload):
        pass

