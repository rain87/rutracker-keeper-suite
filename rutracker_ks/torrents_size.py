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
from bencode import bdecode


size = 0
torrents = scan_folder('/tmp/dl/')
for torrent in torrents:
    with open(torrent) as f:
        data = f.read()
        if data:
            size += torrent_size(bdecode(data))

print '{} torrents: {}'.format(len(torrents), pretty_size(size))
