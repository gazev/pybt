from typing import Set

import asyncio

from client import Client

from tracker import (
    Tracker, 
    PeerResponse,
    TrackerException
)

from file_manager import (
    FileManager, 
    TorrentStatus
)

from torrent_manager import  (
    TorrentManager,
    TorrentStatus
)

from peer import Peer, PeerConnectionError

from piece_algorithms import PieceSelectionAlgorithm

# this must all be moved to different files (instanciation will use factories)
from torrent import TorrentFile
from tracker.http_tracker import HTTPTracker
from piece_algorithms.rarest_first import RarestFirstAlgorithm
from file_manager.single_file_manager import SingleFileManager 


peers_queue: 'Queue[PeerResponse]' = asyncio.Queue(30)
active_peers:   Set[PeerResponse]  = set()


async def run(peers_nr: int, port: int):
    client = Client(max_peers=peers_nr, port=port)

    torrent: TorrentFile = TorrentFile.from_file(path=".stuff/debian.torrent")
    if not torrent['announce'].startswith(b'http'):
        print("Unsupported protocol version! Only HTTP Trackers allowed (for now!)")

    torrent_status: TorrentStatus = TorrentStatus(torrent=torrent)
    file_manager: FileManager = SingleFileManager(torrent=torrent) 
    # make tracker factory when UDP Trackers are supported 
    tracker: Tracker = HTTPTracker(client=client, torrent=torrent, torrent_status=torrent_status)

    tracker_task = asyncio.create_task(tracker_coro(tracker=tracker))

    workers = [
        asyncio.create_task(
            worker_coro(
                torrent=torrent, 
                file_manager=file_manager, 
                client=client
            )
        )
        for _ in range(peers_nr)
    ]

    try:
        await asyncio.sleep(100)
    except asyncio.CancelledError:
        print("\nSIGINT received, terminating")

    tracker_task.cancel()
    for worker in workers:
        worker.cancel()
    
    # wait cancellation
    await tracker_task

    for t in workers:
        await t


async def tracker_coro(tracker: Tracker):
    try:
        while True:
            try:
                fetched_peers: List[PeerResponse]; interval: int
                fetched_peers, interval = await tracker.get_peers()
            except TrackerException as e:
                print(repr(e))
                return

            new_peers = set(fetched_peers) - active_peers

            for peer in new_peers:
                await peers_queue.put(peer) # might block (which is good)
            
            # minimum wait time
            await asyncio.sleep(5)

            if len(active_peers) < 5:
                # continue without waiting if we don't have enough peers
                continue
            
            asyncio.sleep(interval)

    except asyncio.CancelledError:
        await tracker.close()


async def worker_coro(torrent: TorrentFile, file_manager: FileManager, client: Client):
    try:
        while True:
            peer_response: PeerResponse = await peers_queue.get()

            peer = Peer(peer_response, torrent=torrent, client=client)
            try:
                await peer.run()
            except PeerConnectionError as e:
                print(str(e))
                break

    except asyncio.CancelledError:
        print("HERE")
        await peer.end()
        return


try:
    asyncio.run(run(peers_nr=30, port=6881), debug=False)
except KeyboardInterrupt:
    print("Ended this shit")

