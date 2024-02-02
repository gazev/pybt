from typing import Set

import asyncio

from client import Client

from tracker import Tracker, PeerTuple, TrackerException

from file_manager import FileManager, TorrentStatus

from torrent_manager import TorrentManager, TorrentStatus

from peer import Peer, PeerConnectionError

from piece_algorithms import PieceSelectionAlgorithm

# this must all be moved to different files (instanciation will use factories)
from torrent import TorrentFile
from tracker.http_tracker import HTTPTracker
from piece_algorithms.rarest_first import RarestFirstAlgorithm
from file_manager.single_file_manager import SingleFileManager


class Main:
    def __init__(self, peers_nr: int, port: int):
        self.client = Client(max_peers=peers_nr, port=port)
        self.torrent = TorrentFile.from_file(path=".stuff/debian.torrent")

        self.bad_peers = set() # peers that are irresponsive
        self.active_peers = set() # peers currenly connected

        self.pending_peers = asyncio.Queue() # peers waiting for a connection
        self.work_queue = asyncio.Queue() # connected peers to be ran on worker coroutines


    async def run(self):
        if not self.torrent["announce"].startswith(b"http"):
            print("Unsupported protocol version! Only HTTP Trackers allowed")

        torrent_status: TorrentStatus = TorrentStatus(torrent=self.torrent)
        file_manager: FileManager = SingleFileManager(torrent=self.torrent)
        # make tracker factory when UDP Trackers are supported
        tracker: Tracker = HTTPTracker(
            client=self.client, torrent=self.torrent, torrent_status=torrent_status
        )

        # coroutine that periodically fetches peers from tracker
        tracker_task = asyncio.create_task(self.tracker_coro(tracker=tracker))

        # coroutine that connects to peers
        conn_man_task = asyncio.create_task(
            self.conn_manager_coro()
        )

        # coroutine listens for incoming peer connections
        server_task = asyncio.create_task(
            asyncio.start_server(self.server_cb, port=self.client.port)
        )

        await conn_man_task
        # workers = [
        #     asyncio.create_task(
        #         worker_coro(torrent=torrent, file_manager=file_manager, client=client)
        #     )
        #     for _ in range(peers_nr)
        # ]

        # try:
        #     await asyncio.sleep(100)
        # except asyncio.CancelledError:
        #     print("\nSIGINT received, terminating")

        # tracker_task.cancel()
        # for worker in workers:
        #     worker.cancel()

        # # wait cancellation
        # await tracker_task

        # for t in workers:
        #     await t

    async def tracker_coro(self, tracker: Tracker):
        try:
            while True:
                try:
                    peers, interval = await tracker.get_peers()
                except TrackerException as e:
                    print(repr(e))
                    return

                if peers is not None:
                    await self.pending_peers.put(peers)
                    
                await asyncio.sleep(interval)
        
        except asyncio.CancelledError:
            await tracker.close()
    

    async def conn_manager_coro(self):
        """ Coroutine responsible for handshaking peers """
        try:
            while True:
                pending_peers = await self.pending_peers.get()

                tasks = []
                peers = []
                for peer in pending_peers:
                    new_peer = Peer(peer, self.torrent, self.client)
                    tasks.append(new_peer.initialize())
                    peers.append(new_peer)
                
                tasks_g = await asyncio.gather(*tasks, return_exceptions=True)

                for i in range(len(tasks_g)):
                    if isinstance(tasks_g[i], Exception):
                        print(tasks_g[i])
                    else:
                        await self.work_queue.put(peers[i])

        except asyncio.CancelledError:
            pass
            
            
    async def server_cb(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """ Coroutine that accepts incoming peer connections """
        peer_name = reader._transport.get_extra_info('peername') # IP and port

        new_peer = Peer.from_incoming_conn(
            PeerTuple(peer_name[0], peer_name[1]),
            self.torrent,
            self.client,
            reader,
            writer
        )

        try:
            await new_peer.handshake()
        except PeerConnectionError:
            self.bad_peers.add(PeerTuple(peer_name[0], peer_name[1]))
            await new_peer.end()
            return
        
        await self.work_queue.put(new_peer)


    async def worker_coro(
        self, torrent: TorrentFile, file_manager: FileManager, client: Client
    ):
        try:
            while True:
                peer_response: PeerResponse = await self.peers_queue.get()

                peer = Peer(peer_response, torrent=torrent, client=client)
                try:
                    await peer.run()
                except PeerConnectionError as e:
                    self.bad_peers.add(peer_response)
                    print(str(e))
                    break

        except asyncio.CancelledError:
            print("HERE")
            await peer.end()
            return


try:
    obj = Main(30, 6881)
    asyncio.run(obj.run(), debug=False)
except KeyboardInterrupt:
    print("Ended this shit")
