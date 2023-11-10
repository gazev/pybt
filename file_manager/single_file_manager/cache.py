# because annotations may break runtime 
from __future__ import annotations

from functools import wraps
from typing import Callable, List, TYPE_CHECKING

# annotations may break type checkers
if TYPE_CHECKING:
    from piece_manager import PieceManager

def lru_cache(cache_size: int):
    """ This is a LRU Cache decorator which we use to decorate calls to the read
    function.
    
    If desired, the wrapper can be changed to take *args and **kwargs and 
    the cache could be indexed by the arguments hashes to become more generic 
    (like functools lru_cache)
    """
    def decorator(func: Callable[[SingleFileManager, int], bytes]) -> Callable[[SingleFileManager, int], bytes]:
        """ This is our closure environment """
        if cache_size == 0:
            return func

        _cache: dict[int, bytes] = {} 

        @wraps(func)
        def wrapper(instance: SingleFileManager, n: int) -> bytes:
            if len(_cache) >= cache_size:
                _cache.popitem()
            
            if n in _cache:
                return _cache[n]
            
            _cache[n] = func(instance, n)
            return _cache[n]

        return wrapper
    
    return decorator

