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
for i in range(0, len(zero_seeds_torrent_ids)):
    print 'processing {} out of {}'.format(i, len(zero_seeds_torrent_ids))
    id = zero_seeds_torrent_ids[i]
    with open('/tmp/dl/{}.torrent'.format(id), 'wb') as f:
        api.reliable_download_torrent(f, config.keeper_user_id, config.keeper_api_key, id)
