from tracker import TrackerException

class HTTPTrackerException(TrackerException):
    """ Exception raise from HTTPTracker """

class DeadTrackerException(HTTPTrackerException):
    """ Error when a tracker is not working probably because it's dead """

class RequestRejectedException(HTTPTrackerException):
    """ Exception used when tracker doesn't return a 200 response code """
    pass

class BadResponseException(HTTPTrackerException):
    """ Exception used when we don't understand a tracker's response """

class GeneralException(HTTPTrackerException):
    """ Any other exception in which we can't communicate with the tracker """

