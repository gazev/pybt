from typing import Set

import asyncio

from client import Client

from tracker import (
    Tracker, 
    PeerResponse
)

from piece_manager import (
    PieceManager, 
    TorrentStatus
)

from piece_algorithms import PieceSelectionAlgorithm


# this must all be moved to different files (instanciation will use factories)
from torrent import TorrentFile
from tracker.http_tracker import HTTPTracker
from piece_algorithms.rarest_first import RarestFirstAlgorithm
from piece_manager.file_piece_manager import FilePieceManager

class Run:

    async def run(self, peers_nr: int, port: int):
        client: Client = Client(peers_nr=peers_nr, port=port)

        torrent: TorrentFile = TorrentFile.from_file(path="debian.torrent")
        if not torrent['announce'].startswith(b'http'):
            print("Unsupported protocol version! Only HTTP Trackers allowed (for now!)")

        strategy = RarestFirstAlgorithm()
        piece_manager: PieceManager = FilePieceManager(torrent=torrent, piece_sel_strategy=strategy) 
        # make tracker factory when UDP Trackers are supported 
        tracker: Tracker = HTTPTracker(client=client, torrent=torrent, torrent_status=piece_manager)
        # tracker_coro = asyncio.create_task(self.tracker_coro(tracker=tracker))

        await self.tracker_coro(tracker = tracker)
        await tracker.close_session()

        # workers = [
        #     asyncio.create_task(self.worker_coro(torrent=torrent))
        #     for _ in range(self.peers_nr)
        # ]


    async def tracker_coro(self, tracker: Tracker):
        while True:
            try:
                fetched_peers: List[PeerResponse] = await tracker.get_peers()
            except TrackerException as e:
                print(e)

            new_peers = set(fetched_peers) - self.active_peers

            for peer in new_peers:
                await self.peers_queue.add(peer)


    async def worker_coro(self, torrent: TorrentFile, piece_manager: PieceManager):
        pass

asyncio.run(Run().run(peers_nr=30, port=6881), debug=True)
