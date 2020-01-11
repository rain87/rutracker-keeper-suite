#!/usr/bin/env python
# coding=utf-8

import logging
logging.basicConfig(level=logging.INFO)
import sys
import os
reload(sys)
sys.setdefaultencoding('utf-8')

import config
from utils import *
import rutracker_api as api
from bencode import bdecode


size = 0
si_GB = 1000 * 1000 * 1000
desired_size = 1880 * si_GB
desired_size = 0
torrents = scan_folder('/tmp/dl')
dest_dir = '/tmp/dl/sized/'
for torrent in torrents:
    data = None
    with open(torrent) as f:
        data = f.read()
    if data:
        size += torrent_size(bdecode(data))
        if desired_size > 0:
            os.rename(torrent, dest_dir + torrent.split('/')[-1])
            if size >= desired_size:
                break

print '{} torrents: {}'.format(len(torrents), pretty_size(size))
