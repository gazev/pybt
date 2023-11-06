class PiecesWriteBuffer:
    """ 
    This is a class that is used to buffer file writes from FilePieceManager
    """
    def __init__(self, size: int):
        self._size : int = size
        self._buffer : Dict[int, bytes] = {}
    
    def is_full(self) -> bool:
        return len(self._buffer) >= self._size

    def add(self, index: int, piece: bytes) -> None:
        self._buffer[index] = piece
    
    def flush(self, fp):
        # this will save some seek time, also probably save some IO buffer flushes
        sorted_keys = sorted(self.buffer)

        for k in sorted_keys:
            fp.seek(k, 0)
            fp.write(self._buffer[k])
        
