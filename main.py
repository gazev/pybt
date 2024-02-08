from typing import Set

import argparse
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
    def __init__(self, max_peers: int, port: int, path: str):
        self.max_peers = max_peers 
        self.bad_peers = set() # peers that are irresponsive
        self.active_peers = set() # peers currenly connected

        self.pending_peers = asyncio.Queue() # peers ready retrieved from tracker 
        self.peers_awaiting_connection = asyncio.Queue() # peers awaiting connection
        self.work_queue = asyncio.Queue() # connected peers to be ran on worker coroutines

        self.need_peers_lock = asyncio.Lock()
        self.need_peers = asyncio.Condition(self.need_peers_lock)

        self.client = Client(port=port)
        self.torrent = TorrentFile.from_file(path=path)
        self.file_manager = SingleFileManager(self.torrent['info'])
        self.torrent_manager = TorrentManager(self.torrent['info'], self.file_manager)


    async def run(self):
        if not self.torrent["announce"].startswith(b"http"):
            print("Unsupported protocol version! Only HTTP Trackers allowed")
            exit(0)

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

        # tracemalloc.start()
        try:
            await self.torrent_manager.end.wait()
        except (KeyboardInterrupt, asyncio.CancelledError):
            # await self.notify(self.need_peers)
            print("\nSIGINT received, terminating")

        # self.torrent_manager.end.set()
        # snapshot = tracemalloc.take_snapshot()
        # display_top(snapshot)

        tracker_task.cancel()
        conn_man_task.cancel()
        server_task.cancel()

        for worker in workers:
            worker.cancel()

        for worker in conn_workers:
            worker.cancel()
        
        await tracker_task

        return

        

    async def tracker_coro(self, tracker: Tracker):
        try:
            while not self.torrent_manager.end.is_set():
                # TODO
                # We use >= because incoming connections are not accounted
                # since this was only tested behind a NAT
                while len(self.active_peers) >= self.max_peers:
                    await self.wait(cond=self.need_peers)

                try:
                    peers, interval = await tracker.get_peers()
                except TrackerException as e:
                    print(str(e))
                    return

                if peers is not None:
                    await self.pending_peers.put(peers)
                    
                await asyncio.sleep(60)
    
        except asyncio.CancelledError:
            await tracker.close()
    

    async def conn_manager_coro(self):
        """ Coroutine responsible for handshaking peers """
        try:
            while not self.torrent_manager.end.is_set():
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
            while not self.torrent_manager.end.is_set():
                peer_addr = await self.peers_awaiting_connection.get()
                new_peer = Peer(peer_addr, self.torrent, self.client, self.torrent_manager)
                try:
                    await new_peer.initialize()
                except PeerConnectionError as e:
                    print(str(e))
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
            while not self.torrent_manager.end.is_set():
                peer: Peer = await self.work_queue.get()
                self.active_peers.add(peer)

                try:
                    await peer.run()
                except PeerConnectionError as e:
                    print(str(e))
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
    parser = argparse.ArgumentParser(
                        prog = 'pybt',
                        description ='A tiny BitTorrent 1.0 client implementation in Python'
    )

    parser.add_argument('torrentfile', help='absolute or relative path to torrent file')
    parser.add_argument('-p', '--port', type = int,
                            default=6881,
                            help='Port where the client will be accepting connections (default: %(default)s)'
    )

    parser.add_argument('--max-peer', type = int, 
                            default=30, 
                            help='Max number of peers (default: %(default)s)'
    )

    args = parser.parse_args()
    if (args.max_peer < 0 or args.max_peer > 50):
        print("Invalid arguments, max number of peers must be positive a less than 50")
        exit(0)
    if (args.port < 0 or args.port > 2**16):
        print("Invalid port")
        exit(0)

    obj = Main(int(args.max_peer), args.port, args.torrentfile)
    asyncio.run(obj.run(), debug=False)
