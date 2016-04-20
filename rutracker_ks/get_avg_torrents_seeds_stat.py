#!/usr/bin/python
# coding=utf-8

import logging
logging.basicConfig(level=logging.INFO)
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from pymongo import MongoClient
from collections import namedtuple
import datetime
import os
import rutracker_api as api
import qbt_api as qbt
import config


class TorrentStat:
    __slots__ = ['sum', 'cnt']
    def __init__(self, sum):
        self.sum = sum
        self.cnt = 1

    def update_sum(self, sum):
        self.sum += sum
        self.cnt += 1

    def avg(self):
        return float(self.sum) / self.cnt


client = MongoClient()
db = client.rutracker_torrents_stats
stat_records = db.stat.find({'ts': { '$gte': datetime.datetime.now() - datetime.timedelta(weeks=1), '$lt': datetime.datetime.now() } })

ForumStat = namedtuple('ForumStat', 'local remote')
avg_stats = {}

for stat in stat_records:
    forum_ids = stat['forums'].keys()
    for fid in forum_ids:
        if fid not in avg_stats:
            avg_stats[fid] = ForumStat({}, {})
        fstat = stat['forums'][fid]
        avg_stat = avg_stats[fid]

        def update_sum(target, thread_id, cnt):
            if thread_id not in target:
                target[thread_id] = TorrentStat(cnt)
            else:
                target[thread_id].update_sum(cnt)

        map(lambda thread_id: update_sum(avg_stat.local, thread_id, 0), fstat['l']['s0'])
        map(lambda thread_id: update_sum(avg_stat.local, thread_id, 1), fstat['l']['s1'])
        map(lambda thread_id: update_sum(avg_stat.local, thread_id, 2), fstat['l']['s2'])
        map(lambda thread_id: update_sum(avg_stat.local, thread_id, 3), fstat['l']['s3m'])

        map(lambda thread_id: update_sum(avg_stat.remote, thread_id, 0), fstat['r']['s0'])
        map(lambda thread_id: update_sum(avg_stat.remote, thread_id, 1), fstat['r']['s1'])
        map(lambda thread_id: update_sum(avg_stat.remote, thread_id, 2), fstat['r']['s2'])
        map(lambda thread_id: update_sum(avg_stat.remote, thread_id, 3), fstat['r']['s3m'])

for fid, stat in avg_stats.iteritems():
    print 'Stat for {}:'.format(fid)

    def trim_stat(stat):
        remove_keys = [ k for k, v in stat.iteritems() if v.cnt <= 24 * 5 ]
        for key in remove_keys:
            del stat[key]

    trim_stat(stat.local)
    trim_stat(stat.remote)

    #local_sorted = sorted(stat.local.items(), key=lambda tpl: -tpl[1].avg())
    #remote_sorted = sorted(stat.remote.items(), key=lambda tpl: tpl[1].avg())

    local_strong = [str(tpl[0]) for tpl in stat.local.items() if tpl[1].avg() > 2.5]
    remote_dying = [str(tpl[0]) for tpl in stat.remote.items() if tpl[1].avg() < 1]

    local_strong = [sha1.lower() for sha1 in api.get_tor_hash(local_strong).values() if sha1]
    remote_dying = api.get_tor_hash(remote_dying)

    local_strong = [sha1 for sha1 in local_strong if qbt.is_torrent_exists(sha1)]
    remote_dying = [kv[0] for kv in remote_dying.iteritems() if not qbt.is_torrent_exists(kv[1])]

    print "Weak local: {}".format(sum(int(tpl[1].avg() < 1) for tpl in stat.local.items()))
    print "Strong local: {}".format(len(local_strong))
    print "Dying remote: {}".format(len(remote_dying))
    continue

    qbt.remove_torrents(local_strong)

    for i in range(0, len(remote_dying)):
        print 'processing {} out of {}'.format(i, len(remote_dying))
        id = remote_dying[i]
        with open('/tmp/dl/{}.torrent'.format(id), 'wb') as f:
            api.reliable_download_torrent(f, config.keeper_user_id, config.keeper_api_key, id)

torrents = config.torrents_source(*config.torrents_source_args)
torrents_meta = []

infohashes = [os.path.splitext(os.path.basename(torrent_fname))[0] for torrent_fname in torrents]
thread_ids = api.get_topic_id(infohashes)
orphaned_local = [sha1 for sha1 in thread_ids.keys() if thread_ids[sha1] is None]
print 'Orphaned local: {}'.format(len(orphaned_local))
