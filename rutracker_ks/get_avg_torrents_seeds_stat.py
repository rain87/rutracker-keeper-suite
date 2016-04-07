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
stat_records = db.stat.find({'ts': { '$gte': datetime.datetime.now() - datetime.timedelta(days=1), '$lt': datetime.datetime.now() } })

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
    local_sorted = sorted(stat.local.items(), key=lambda tpl: -tpl[1].avg())
    remote_sorted = sorted(stat.remote.items(), key=lambda tpl: tpl[1].avg())

    print 'Local:'
    for stat in local_sorted:
        print '{}: {}'.format(stat[0], stat[1].avg())

    print 'Remote:'
    for stat in remote_sorted:
        print '{}: {}'.format(stat[0], stat[1].avg())
    print ''

