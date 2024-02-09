from typing import Protocol

import bitarray
import asyncio

from hashlib import sha1

from torrent import InfoDict
from protocol import MessageOP 
from protocol import (
    Handshake,
    Choke,
    Unchoke,
    Interested,
    NotInterested,
    Have,
    Request,
    PieceMessage,
    Cancel
)




class PeerState:
    def __init__(self, ctx):
        self._ctx = ctx
    

    async def do_work(self):
        """ This is the important subtyping """
        raise NotImplementedError


    def change_state(self, state: str):
        raise NotImplementedError


    async def handle_message(self, op_code: str, payload: bytes):
        match op_code:
            case MessageOP.KEEP_ALIVE:
                pass # simply resets timeout counter
            case MessageOP.CHOKE:
                self.change_state('choked')
            case MessageOP.UNCHOKE:
                self.change_state('unchoked')
            case MessageOP.INTERESTED:
                self.handle_interested()
            case MessageOP.NOT_INTERESTED:
                self.handle_not_interested()
            case MessageOP.HAVE:
                self.handle_have(payload)
            case MessageOP.BITFIELD:
                self.handle_bitfield(payload)
            case MessageOP.PIECE:
                await self.handle_piece(payload)
            case MessageOP.CANCEL:
                self.handle_cancel(payload)
            case default:
                pass
    

    def handle_interested(self):
        pass


    def handle_not_interested(self):
        pass


    def handle_have(self, payload: int):
        try:
            self._ctx.bitfield[payload] = 1
        except IndexError:
            pass


    def handle_bitfield(self, payload: bytes):
        if (len(payload) * 8) != len(self._ctx.bitfield):
            raise PeerConnectionError("Invalid Bitfield received, connection dropped")

        new_bitfield = bitarray.bitarray()
        self._ctx.bitfield = new_bitfield
        self._ctx.bitfield.frombytes(payload)


    def handle_piece(self, payload: bytes):
        pass
        

    def handle_cancel(self, payload: bytes):
        pass


class ChokedNotInterested(PeerState):
    def change_state(self, state):
        if state == 'interested':
            self._ctx.change_state(ChokedInterested(self._ctx))
        elif state == 'unchoked':
            self._ctx.change_state(UnchokedNotInterested(self._ctx))
    
    async def do_work(self):
        # check if we have interest
        piece = self._ctx.torrent_manager.get_pieces(self._ctx.bitfield)
        if piece is not None:
            self._ctx.torrent_manager.put_pieces(piece)
            self.change_state('interested')
            await self._ctx.send_message(Interested())
        

class ChokedInterested(PeerState):
    def change_state(self, state):
        if state == 'not interested':
            self._ctx.change_state(ChokedNotInterested(self._ctx))
        elif state == 'unchoked':
            self._ctx.change_state(UnchokedInterested(self._ctx))

    async def do_work(self):
        # simply await for unchoke
        pass
        

class UnchokedNotInterested(PeerState):
    def change_state(self, state):
        if state == 'interested':
            self._ctx.change_state(UnchokedInterested(self._ctx))
        elif state == 'choked':
            self._ctx.change_state(ChokedNotInterested(self._ctx))
    
    async def do_work(self):
        # check if we have interest
        piece = self._ctx.torrent_manager.get_pieces(self._ctx.bitfield)
        if piece:
            self._ctx.torrent_manager.put_pieces(piece)
            self.change_state('interested')
            # do the work right after we change our internal state
            await self._ctx.send_message(Interested())
            await self._ctx._state.do_work()
        

class UnchokedInterested(PeerState):
    def __init__(self, ctx):
        super().__init__(ctx)
        self._scheduled_piece = None
        self._piece_handler = None


    def change_state(self, state):
        if state == 'not interested':
            self._ctx.change_state(UnchokedNotInterested(self._ctx))
        elif state == 'choked':
            self._ctx.change_state(ChokedInterested(self._ctx))


    async def do_work(self):
        # if we are already waiting for pieces
        if self._scheduled_piece is not None:
            return

        # get piece to request to peer
        self._scheduled_piece = self._ctx.torrent_manager.get_pieces(self._ctx.bitfield)
        # print(f"Got piece {self._scheduled_piece}")
        if self._scheduled_piece is None:
            self.change_state('not interested')
            return
        
        # enqueue block requests
        self._piece_handler = PieceHandler(self._ctx, self._scheduled_piece, self._ctx.torrent['info'])
        await self._piece_handler.enqueue_requests()
    

    async def handle_piece(self, payload):
        # we are not waiting for pieces
        if self._scheduled_piece is None:
            return
        
        await self._piece_handler.receive_block(payload)
    

    def _reset(self):
        self._scheduled_piece = None
        self._piece_handler = None
        

class PieceHandler:
    BLOCK_SIZE = 16384 # 16 KiB

    def __init__(self, ctx, piece_nr: int, meta_info: InfoDict):
        self._ctx = ctx

        self._piece_nr = piece_nr
        self._buff = bytearray(meta_info['piece length'])
        self._retr_offset = 0
        self._hash = meta_info.get_hash(piece_nr)

        self._piece_len = meta_info['piece length']
        self._total_blocks = meta_info['piece length'] / self.BLOCK_SIZE
        self._retr_blocks = 0
        self._enqueued = 0
        

    async def enqueue_requests(self):
        """ Enqueue block requests for a piece """
        offset = self._retr_offset 
        for _ in range(5): # enqueue 5 requests
            # if all blocks are requested
            if offset >= self._piece_len:
                return

            await self._ctx.send_message(Request(self._piece_nr, offset, self.BLOCK_SIZE))
            self._enqueued += 1
            offset += self.BLOCK_SIZE

   
    async def receive_block(self, payload):
        idx, offset, data = PieceMessage.decode(payload)

        if idx != self._piece_nr:
            return
        
        self._buff[offset: offset + self.BLOCK_SIZE] = data

        self._retr_blocks += 1
        if self._retr_blocks == self._total_blocks:
            self.save_piece()
            await asyncio.sleep(.1)
            return

        self._retr_offset += self.BLOCK_SIZE
        self._enqueued -= 1

        if self._enqueued == 0:
            await self.enqueue_requests()
            

    def save_piece(self):
        self._ctx._state._reset()

        if sha1(self._buff).digest() != self._hash:
            self._ctx.torrent_manager.put_pieces(self._piece_nr)
            return

        self._ctx.torrent_manager.save_piece(self._piece_nr, self._buff)



