from typing import List
from tracker import PeerTuple

from ipaddress import ip_address
from struct import unpack

def peer_lst_f_raw_str(raw_str: bytes) -> List[PeerTuple]:
    # DO NOT use list comprehension for this, it is unreadable
    peers = []
    for i in range(0, len(raw_str), 6):
        peers.append(
            PeerTuple(
                ip = _decode_ip(raw_str[i:i+4]), 
                port = _decode_port(raw_str[i+4:i+6])
            )
        )

    return peers


def _decode_ip(data: bytes) -> str:
    return str(ip_address(data))


def _decode_port(data: bytes) -> int:
    return unpack(">H", data)[0]   