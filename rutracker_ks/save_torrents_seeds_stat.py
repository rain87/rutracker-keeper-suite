#!/usr/bin/env python
# coding=utf-8

import logging
logging.basicConfig(level=logging.INFO)
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
from pymongo import MongoClient

import config
from utils import *
import rutracker_api as api
import datetime
import qbt_api as qbt


def compact_torrent_stats(stats):
    return {
        's0': [thread_id for thread_id in stats.keys() if stats[thread_id] == 0],
        's1': [thread_id for thread_id in stats.keys() if stats[thread_id] == 1],
        's2': [thread_id for thread_id in stats.keys() if stats[thread_id] == 2],
        's3m': [thread_id for thread_id in stats.keys() if stats[thread_id] >= 3]
    }

torrents = config.torrents_source(*config.torrents_source_args)
torrents_meta = []

# first, fetch topic ids by infohash
infohashes = [os.path.splitext(os.path.basename(torrent_fname))[0] for torrent_fname in torrents]
thread_ids = set(api.get_topic_id(infohashes).values())

db_record = {
    'ts': datetime.datetime.now(),
    'forums': {}
}

# fetch torrents' stats from server
for forum_id in config.keeped_forums:
    torrents_stats = api.get_forum_torrents_status(forum_id)
    torrents_stats = { int(id): torrents_stats[id] for id in torrents_stats.keys() }

    # form stat for local torrents
    local_torrents = { thread_id: torrents_stats[thread_id][1]
        for thread_id in thread_ids
        if thread_id in torrents_stats
    }

    # and remote stat, consisted of dying torrents absent locally
    remote_torrents = { thread_id: torrents_stats[thread_id][1]
        for thread_id in torrents_stats.keys()
        if thread_id not in thread_ids and
            len(torrents_stats[thread_id]) == 2 and
            torrents_stats[thread_id][1] < 3 and
            torrents_stats[thread_id][0] in (2, 8)
    }

    db_record['forums'][str(forum_id)] = {
        'l': compact_torrent_stats(local_torrents),
        'r': compact_torrent_stats(remote_torrents)
    }

client = MongoClient()
db = client.rutracker_torrents_stats
db.stat.insert_one(db_record)
