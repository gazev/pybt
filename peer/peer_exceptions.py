class PeerConnectionError(Exception):
    """Class to communicate error while communicating with a peer"""


class PeerConnectionOpenError(PeerConnectionError):
    """Error when we fail to open a connection to the peer"""


class PeerConnectionReadError(PeerConnectionError):
    """Error when reading from peer connection"""


class PeerConnectionHandshakeError(PeerConnectionError):
    """Error when we fail to open a connection to the peer"""
