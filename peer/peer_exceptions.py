class PeerConnectionError(Exception):
    """ Exception raised from PeerConnection """


class PeerConnectionOpenError(PeerConnectionError):
    """ Error when we fail to open a connection to the peer """


class PeerConnectionReadError(PeerConnectionError):
    """ Error when receiving data from peer """


class PeerConnectionHandshakeError(PeerConnectionError):
    """ Error when we fail to open a connection to the peer """
