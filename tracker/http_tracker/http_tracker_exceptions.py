from tracker import TrackerException

class HTTPTrackerException(TrackerException):
    pass

class DeadTrackerException(HTTPTrackerException):
    """
    Exception that will indicate a Tracker is not working, probably because
    it's dead, down or simply isn't a Tracker 
    """
    pass

class RequestRejectedException(HTTPTrackerException):
    """
    Exception used when Tracker doesn't return a 200 response code
    """
    pass

class BadResponseException(HTTPTrackerException):
    """
    Exception used when the Tracker responds but we can't make any sense of the
    response
    """

class GeneralException(HTTPTrackerException):
    """ A general exceptino, mostly means the Tracker couldn't be resolved for
    various reasons such as malformed URL. 
    """


