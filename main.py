from typing import Set
import asyncio


# interfaces for annotations
from tracker import (
    Tracker, 
    PeerResponse
)


from piece_manager import (
    PieceManager, 
    TorrentStatus
)


from piece_algorithms import PieceSelectionAlgorithm


# actually used classes
from torrent import TorrentFile
from tracker.http_tracker import HTTPTracker
from piece_algorithms.rarest_first import RarestFirstAlgorithm
from piece_manager.file_piece_manager import FilePieceManager


class Run:
    def __init__(self, peers_nr: int, port: int):
        self.peers_queue = asyncio.Queue(30)
        self.fetched_peers: Set[PeerResponse] = set()
        self.active_peers:  Set[PeerResponse] = set()

        self.peers_nr: int = peers_nr
        self.port: int = port

    async def run(self):
        torrent: TorrentFile = TorrentFile.from_file(path="a test file.txt.torrent")
        if not torrent['announce'].startswith(b'http'):
            print("Unsupported protocol version! Only HTTP Trackers allowed (for now!)")

        # TODO algorithm selected from config
        strategy = RarestFirstAlgorithm()
        piece_manager: PieceManager = FilePieceManager(torrent=torrent, piece_sel_strategy=strategy) 
        # make tracker factory when UDP Trackers are supported 
        tracker: Tracker = HTTPTracker(torrent=torrent, torrent_status=piece_manager)
        # tracker_coro = asyncio.create_task(self.tracker_coro(tracker=tracker))

        await tracker.close_session()

        # workers = [
        #     asyncio.create_task(self.worker_coro(torrent=torrent))
        #     for _ in range(self.peers_nr)
        # ]


    async def tracker_coro(self, tracker: Tracker, torrent_status: TorrentStatus):
        pass

    async def worker_coro(self, torrent: TorrentFile, piece_manager: PieceManager):
        pass

asyncio.run(Run(peers_nr=30, port=6881).run(), debug=True)
