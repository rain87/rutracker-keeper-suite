import logging
from bencode import bdecode
import utils
import os
import requests


LOGGER = logging.getLogger(__name__)


def is_torrent_completed(sha1):
    with open('/home/rain87/.local/share/data/qBittorrent/BT_backup/{}.fastresume'.format(sha1), 'rb') as f:
        fresume = bdecode(f.read())
    return fresume['pieces'].find('\x00') == -1

def is_torrent_exists(sha1):
    return os.path.exists('/home/rain87/.local/share/data/qBittorrent/BT_backup/{}.torrent'.format(sha1.lower()))

def remove_torrents(sha1):
    if not sha1:
        return
    if not isinstance(sha1, list):
        sha1 = [sha1]
    r = requests.post('http://localhost:8080/command/deletePerm',
        headers={'content-type': 'application/x-www-form-urlencoded',
                 'Referer': 'http://localhost:8080/'},
        data='hashes=' + '%7c'.join(sha1))
    assert r.status_code == 200, 'QBittorrent status code is not ok: {}'.format(r.text)
