from typing import Protocol, List

class PieceSelectionAlgorithm(Protocol):
    """ Algorithms  for piece selection. Strategies used by FilePieceManager """

    # initialize the algorithm state
    def initialize(self, nr_pieces: int):
        raise NotImplementedError

    # update every time a new peer sends a bitfield message 
    def update_new_bitfield(self, bitfield: List[bool]):
        raise NotImplementedError
    
    # update whenever a peer signals it got a new piece
    def update_new_piece(self, index: int):
        raise NotImplementedError

    # get desired piece 
    def get_next_piece(self):
        raise NotImplementedError

