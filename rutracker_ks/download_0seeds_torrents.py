#!/usr/bin/env python
# coding=utf-8

import logging
logging.basicConfig(level=logging.INFO)
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import config
from utils import *
import rutracker_api as api
from qbt_api import is_torrent_exists

for f in config.keeped_forums[3:]:
    data = api.get_forum_torrents_status(f)
    zero_seeds_torrent_ids = [thread for thread in data.keys()
        if len(data[thread]) > 1 and data[thread][1] == 0 and data[thread][0] in (2, 8)]
    print len(zero_seeds_torrent_ids)

    zero_seeds_torrent_hashes = api.get_tor_hash(zero_seeds_torrent_ids)
    zero_seeds_torrent_ids = [torrent_id for torrent_id in zero_seeds_torrent_ids
        if not is_torrent_exists(zero_seeds_torrent_hashes[torrent_id].lower())]
    print len(zero_seeds_torrent_ids)

    for i in range(0, len(zero_seeds_torrent_ids)):
        print 'processing {} out of {}'.format(i, len(zero_seeds_torrent_ids))
        id = zero_seeds_torrent_ids[i]
        with open('/tmp/dl/{}.torrent'.format(id), 'wb') as f:
            api.reliable_download_torrent(f, config.keeper_user_id, config.keeper_api_key, id)
