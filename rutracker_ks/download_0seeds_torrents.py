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

data = api.get_forum_torrents_status(2092)
#print len(data.keys())
zero_seeds_torrent_ids = [thread for thread in data.keys()
    if len(data[thread]) == 2 and data[thread][1] == 0 and data[thread][0] in (2, 8)]
print len(zero_seeds_torrent_ids)

with open('/tmp/sha1', 'rt') as f:
    already_have_downloads = set(f.read().splitlines())

zero_seeds_torrent_hashes = api.get_tor_hash(zero_seeds_torrent_ids)
zero_seeds_torrent_ids = [torrent_id for torrent_id in zero_seeds_torrent_ids
    if zero_seeds_torrent_hashes[torrent_id].lower() not in already_have_downloads]
print len(zero_seeds_torrent_ids)

for i in range(0, len(zero_seeds_torrent_ids)):
    print 'processing {} out of {}'.format(i, len(zero_seeds_torrent_ids))
    id = zero_seeds_torrent_ids[i]
    with open('/tmp/dl/{}.torrent'.format(id), 'wb') as f:
        api.reliable_download_torrent(f, config.keeper_user_id, config.keeper_api_key, id)

