from typing import Protocol
from protocol import MessageOP 

import bitarray

from protocol import (
    Handshake,
    Choke,
    Unchoke,
    Interested,
    NotInterested,
    Have,
    Request,
    Cancel
)


class PeerState:
    def __init__(self, ctx):
        self._ctx = ctx
    
    def do_work(self):
        """ This is the important subtyping """
        raise NotImplementedError


    def handle_message(self, op_code: str, payload: bytes):
        match op_code:
            case MessageOP.KEEP_ALIVE:
                pass
            case MessageOP.CHOKE:
                print("choked msg")
                self.change_state('choked')
            case MessageOP.UNCHOKE:
                print("unchoked msg")
                self.change_state('unchoked')
            case MessageOP.INTERESTED:
                print("interested msg")
                self.change_state('interested')
            case MessageOP.NOT_INTERESTED:
                print("not interested msg")
                self.change_state('not interested')
            case MessageOP.HAVE:
                print("have message")
                self.handle_have(payload)
            case MessageOP.BITFIELD:
                print("bitfield message")
                self.handle_bitfield(payload)
            case MessageOP.PIECE:
                self.handle_piece(payload)
            case MessageOP.CANCEL:
                self.handle_cancel(payload)
            case default:
                pass
    

    def handle_have(self, payload):
        self._ctx.piece_manager.update_peer(self._ctx, payload)
    

    def handle_bitfield(self, payload):
        print(payload)
        a = bitarray.bitarray().frombytes(payload)
        print(a)
        self._ctx.piece_manager.register_peer(self._ctx, payload)


    def handle_piece(self, payload):
        raise NotImplementedError


    def handle_cancel(self, payload):
        pass
        

class ChokedNotInterested(PeerState):
    def change_state(self, state):
        if state == 'interested':
            print("going interested")
            self._ctx.change_state(ChokedInterested(self._ctx))
        elif state == 'unchoked':
            print("going unchoked")
            self._ctx.change_state(UnchokedNotInterested(self._ctx))


class ChokedInterested(PeerState):
    def change_state(self, state):
        if state == 'not interested':
            self._ctx.change_state(ChokedNotInterested(self._ctx))
        elif state == 'unchoked':
            self._ctx.change_state(UnchokedInterested(self._ctx))


class UnchokedNotInterested(PeerState):
    def change_state(self, state):
        if state == 'interested':
            self._ctx.change_state(UnchokedInterested(self._ctx))
        elif state == 'choked':
            self._ctx.change_state(ChokedNotInterested(self._ctx))


class UnchokedInterested(PeerState):
    def change_state(self, state):
        if state == 'not interested':
            self._ctx.change_state(ChokedUninterested(self._ctx))
        elif state == 'unchoked':
            self._ctx.change_state(UnchokedNotInterested(self._ctx))

