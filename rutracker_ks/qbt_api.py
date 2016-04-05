import logging
from bencode import bdecode
import utils


LOGGER = logging.getLogger(__name__)


def is_torrent_completed(sha1):
    with open('/home/rain87/.local/share/data/qBittorrent/BT_backup/{}.fastresume'.format(sha1), 'rb') as f:
        fresume = bdecode(f.read())
    return fresume['pieces'].find('\x00') == -1

