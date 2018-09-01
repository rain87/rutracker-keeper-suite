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
from bencode import bdecode, bencode
import re

cnt = 0
torrents = scan_folder('/tmp/BT_backup')
for torrent in torrents:
    cnt += 1
    if cnt % 100 == 0:
        print('Processing {}'.format(cnt))
    tracker = ''
    with open(torrent) as f:
        data = bdecode(f.read())
        tracker = re.sub('http://(bt\d?).*?/', 'http://\\1.rutracker.cx/', data['announce'])
        data['announce'] = tracker
        #data['announce-list'] = [ tracker ]
        if 'announce-list' in data:
            del data['announce-list']
    with open(torrent, 'w') as f:
        f.write(bencode(data))

    fastresume = torrent[:-len('.torrent')] + '.fastresume'
    with open(fastresume) as f:
        data = bdecode(f.read())
        #data['trackers'] = [ tracker ]
        del data['trackers']
    with open(fastresume, 'w') as f:
        f.write(bencode(data))
