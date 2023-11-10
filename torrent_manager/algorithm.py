from typing import Protocol, Any

class Algorithm(Protocol):
    """ Class for llgorithms used for piece selection """
    def initialize(self):
        raise NotImplementedError

    def get_piece_rarest_piece(self):
        raise NotImplementedError

    def update(self, update: Any):
        raise NotImplementedError