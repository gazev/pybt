from typing import Any

class InvalidResponseException(KeyError):
    """ If Tracker isn't providing us with specified keys. If this happens it is
    most likely the Tracker is broken as it isn't obeying to the BEP 1.0 spec
    """

class HTTPTrackerResponse:
    __resp_keys = {'peers', 'interval'}
    __failure_keys = {'failure reason'}

    def __init__(self, **kwargs):
        self._inner_dict = kwargs

        if self.__resp_keys - set(kwargs.keys()):
            if self.__failure_keys - set(kwargs.keys()):
                raise InvalidResponseException('Invalid keys in Tracker response')
            
            return
            
        if not isinstance(kwargs['peers'], bytes):
            raise InvalidResponseException('Invalid "peers" key')
        
        if not isinstance(kwargs['interval'], int):
            raise InvalidResponseException('Invalid "interval" key')

    
    def __getitem__(self, key: str) -> Any:
        if key in self._inner_dict:
            return self._inner_dict[key]
        
        return None
        
