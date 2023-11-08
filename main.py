from typing import Set

import asyncio

from client import Client

from tracker import (
    Tracker, 
    PeerResponse,
    TrackerException
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
    def __init__(self):
        self.peers_queue: 'Queue[PeerResponse]' = asyncio.Queue(30)
        self.active_peers:   Set[PeerResponse]  = set()

    async def run(self, peers_nr: int, port: int):
        client: Client = Client(max_peers=peers_nr, port=port)

        torrent: TorrentFile = TorrentFile.from_file(path=".stuff/debian.torrent")
        if not torrent['announce'].startswith(b'http'):
            print("Unsupported protocol version! Only HTTP Trackers allowed (for now!)")

        strategy = RarestFirstAlgorithm()
        piece_manager: PieceManager = FilePieceManager(torrent=torrent, piece_sel_strategy=strategy) 
        # make tracker factory when UDP Trackers are supported 
        tracker: Tracker = HTTPTracker(client=client, torrent=torrent, torrent_status=piece_manager)
        # tracker_coro = asyncio.create_task(self.tracker_coro(tracker=tracker))


        tracker_coro = asyncio.create_task(self.tracker_coro(tracker=tracker))

        workers = [
            asyncio.create_task(self.worker_coro(torrent=torrent, piece_manager=piece_manager))
            for _ in range(peers_nr)
        ]

        try:
            await asyncio.sleep(100)
        except asyncio.CancelledError:
            print("\nSIGINT received, terminating")

        await tracker.close_session()

        tracker_coro.cancel()
        for worker in workers:
            worker.cancel()


    async def tracker_coro(self, tracker: Tracker):
        try:
            while True:
                try:
                    fetched_peers: List[PeerResponse]
                    interval: int
                    fetched_peers, interval = await tracker.get_peers()
                except TrackerException as e:
                    # this will halt execution
                    print(e)

                new_peers = set(fetched_peers) - self.active_peers

                for peer in new_peers:
                    await self.peers_queue.put(peer) # might block (which is good)
                
                # minimum wait time
                await asyncio.sleep(5)

                if len(self.active_peers) < 5:
                    # continue without waiting if we don't have enough peers
                    continue
                
                asyncio.sleep(interval)
        except asyncio.CancelledError:
            return


    async def worker_coro(self, torrent: TorrentFile, piece_manager: PieceManager):
        try:
            while True:
                peer: PeerResponse = await self.peers_queue.get()
                print(f"{peer.ip}:{peer.port}", flush=True)

        except asyncio.CancelledError:
            return


try:
    asyncio.run(Run().run(peers_nr=30, port=6881), debug=True)
except KeyboardInterrupt:
    print("Ended this shit")
