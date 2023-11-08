from typing import Protocol, List

class PieceSelectionAlgorithm(Protocol):
    """ Algorithms  for piece selection. Strategies used by FilePieceManager
    """
    # Initialize the algorithm state
    def initialize(self, nr_pieces: int):
        raise NotImplementedError

    # Update every time a new peer sends a bitfield message 
    def update_new_bitfield(self, bitfield: List[bool]):
        raise NotImplementedError
    
    # Update whenever a peer signals it got a new piece
    def update_new_piece(self, index: int):
        raise NotImplementedError

    # Get desired piece 
    def get_next_piece(self):
        raise NotImplementedError

