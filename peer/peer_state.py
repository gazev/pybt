from typing import Protocol

class PeerState:
    def __init__(self, ctx):
        self._ctx = ctx
    
    def change_state(self, state: str):
        self._ctx.change_state(state)


# Initial state
class ChokedUninterested(PeerState):
    def __init__(self, ctx):
        pass


