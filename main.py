from typing import Set

import asyncio

from client import Client

from tracker import Tracker, PeerAddr, TrackerException

from file_manager import FileManager, TorrentStatus

from torrent_manager import TorrentManager

from peer import Peer, PeerConnectionError

from piece_algorithms import PieceSelectionAlgorithm

# this must all be moved to different files (instanciation will use factories)
from torrent import TorrentFile
from tracker.http_tracker import HTTPTracker
from piece_algorithms.rarest_first import RarestFirstAlgorithm
from file_manager.single_file_manager import SingleFileManager


class Main:
    def __init__(self, max_peers: int, port: int):
        self.client = Client(max_peers=max_peers, port=port)
        self.torrent = TorrentFile.from_file(path=".stuff/debian.torrent")
        self.torrent_manager = TorrentManager(self.torrent['info'])
        self.max_peers = max_peers 

        self.bad_peers = set() # peers that are irresponsive
        self.active_peers = set() # peers currenly connected

        self.pending_peers = asyncio.Queue() # peers ready retrieved from tracker 
        self.peers_awaiting_connection = asyncio.Queue() # peers awaiting connection
        self.work_queue = asyncio.Queue() # connected peers to be ran on worker coroutines

        self.need_peers_lock = asyncio.Lock()
        self.need_peers = asyncio.Condition(self.need_peers_lock)


    async def run(self):
        if not self.torrent["announce"].startswith(b"http"):
            print("Unsupported protocol version! Only HTTP Trackers allowed")

        # make tracker factory when UDP Trackers are supported
        tracker: Tracker = HTTPTracker(
            client=self.client, torrent=self.torrent
        )

        # coroutine that periodically fetches peers from tracker
        tracker_task = asyncio.create_task(self.tracker_coro(tracker=tracker))

        # coroutine that connects to peers
        conn_man_task = asyncio.create_task(
            self.conn_manager_coro()
        )

        conn_workers = [
            asyncio.create_task(self.conn_worker()) for _ in range(self.max_peers)
        ]

        # coroutine listens for incoming peer connections
        server_task = asyncio.create_task(
            asyncio.start_server(self.server_cb, port=self.client.port)
        )


        workers = [
            asyncio.create_task(self.worker_coro())
            for _ in range(self.max_peers)
        ]

        try:
            while True:
                print(len(self.active_peers))
                print(len(self.bad_peers))
                await asyncio.sleep(5)
        except KeyboardInterrupt:
            print("\nSIGINT received, terminating")

        tracker_task.cancel()
        conn_man_task.cancel()
        server_task.cancel()

        for worker in workers:
            worker.cancel()

        for worker in conn_workers:
            worker.cancel()
        
        for t in workers:
            await t

        for t in conn_workers:
            await t

        await tracker_task
        await conn_man_task

        await server_task

        print("it's ove")

        

    async def tracker_coro(self, tracker: Tracker):
        try:
            while True:
                # TODO
                # We use >= because incoming connections are not accounted
                # since this was only tested behind a NAT
                while len(self.active_peers) >= self.max_peers:
                    await self.wait(cond=self.need_peers)

                try:
                    peers, interval = await tracker.get_peers()
                except TrackerException as e:
                    print(repr(e))
                    return

                if peers is not None:
                    await self.pending_peers.put(peers)
                    
                await asyncio.sleep(5)
    
        except asyncio.CancelledError:
            await tracker.close()
    

    async def conn_manager_coro(self):
        """ Coroutine responsible for handshaking peers """
        try:
            while True:
                pending_peers = await self.pending_peers.get()

                if len(self.active_peers) >= self.max_peers:
                    continue

                for peer_addr in pending_peers:
                    # peer marked as bad or already active 
                    if not {peer_addr} - self.bad_peers - self.active_peers:
                        continue

                    # new_peer = Peer(peer, self.torrent, self.client)
                    await self.peers_awaiting_connection.put(peer_addr)

        except asyncio.CancelledError:
            pass


    async def conn_worker(self):
        try:
            while True:
                peer_addr = await self.peers_awaiting_connection.get()
                new_peer = Peer(peer_addr, self.torrent, self.client, self.torrent_manager)
                try:
                    await new_peer.initialize()
                except PeerConnectionError as e:
                    print(repr(e))
                    self.bad_peers.add(peer_addr)
                    continue
                
                await self.work_queue.put(new_peer)
        
        except asyncio.CancelledError:
            pass

            
    async def server_cb(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """ Coroutine that accepts incoming peer connections """
        peer_name = reader._transport.get_extra_info('peername') # IP and port

        new_peer = Peer.from_incoming_conn(
            PeerAddr(peer_name[0], peer_name[1]),
            self.torrent,
            self.client,
            reader,
            writer
        )

        try:
            await new_peer.handshake()
        except PeerConnectionError:
            self.bad_peers.add(new_peer)
            await new_peer.end()
            return
        
        await self.work_queue.put(new_peer)


    async def worker_coro(self):
        try:
            while True:
                peer: Peer = await self.work_queue.get()
                self.active_peers.add(peer)

                try:
                    await peer.run()
                except PeerConnectionError as e:
                    print(repr(e))
                    self.active_peers.remove(peer)
                    if (len(self.active_peers) < self.max_peers):
                        await self.notify(self.need_peers)
                except asyncio.CancelledError:
                    return
                finally:
                    await peer.end()


        except asyncio.CancelledError:
            pass


    async def wait(self, cond: asyncio.Condition):
        """ Wait on a condition atomically """
        try:
            await cond.acquire()
            await cond.wait()
        except asyncio.CancelledError:
            if cond.locked():
                cond.release() 
            raise
    
    async def notify(self, cond: asyncio.Condition):
        """ Atomically notify of a condition """
        try:
            await cond.acquire()
            cond.notify()
            cond.release()
        except asyncio.CancelledError:
            if cond.locked():
                cond.release()
            raise



if __name__ == '__main__':
    obj = Main(30, 6881)
    asyncio.run(obj.run(), debug=False)
