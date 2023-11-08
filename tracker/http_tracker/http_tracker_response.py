class InvalidResponseException(KeyError):
    """
    If Tracker isn't providing us with specified keys. If this happens it is
    most likely the Tracker is broken as it isn't obeying to the BEP 1.0 spec
    """

class HTTPTrackerResponse:
    def __init__(self, **kwargs):
        # if the request failed
        if 'failure reason' in kwargs:
            self.failure_reason = failure_reason.decode('utf-8')
            self.complete   = 0
            self.incomplete = 0
            self.interval   = 0 
            self.peers      = b''
            return
        
        self.failure_reason = None
        
        peers = kwargs.get('peers')
        if peers is None:
            raise InvalidResponseException("No peers key was provided")
 
        if 'interval' in kwargs:
            self.interval = kwargs['interval']
        elif 'min interval' in kwargs:
            self.interval = kwargs['min interval']
        else:
            self.interval = 30 # default interval if not specified

        complete = kwargs.get('complete')
        if complete is None:
            complete = 0 
        
        incomplete = kwargs.get('incomplete')
        if incomplete is None:
            incomplete = 0
       
        self.complete = complete
        self.incomplete = incomplete
        self.peers = peers
        
