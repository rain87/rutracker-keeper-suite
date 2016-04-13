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
import datetime
import qbt_api as qbt
from cStringIO import StringIO


RUTRACKER_META_KEY = 'rutracker_meta_v1'

def fetch_rutracker_meta(torrents):
    # first, fetch topic ids by infohash
    hashes = { torrent_hash(torrent_dict): torrent_dict for torrent_dict in torrents }
    thread_ids = api.get_topic_id(hashes.keys())
    for infohash, torrent_dict in hashes.iteritems():
        if infohash in thread_ids and thread_ids[infohash] is not None:
            torrent_dict[RUTRACKER_META_KEY] = {
                "thread_id": thread_ids[infohash]
            }
        else:
            torrent_dict[RUTRACKER_META_KEY] = 0

    # remove torrents that has no corresponding thread at tracker
    unrelated_indices = [i for i in range(0, len(torrents))
        if isinstance(torrents[i][RUTRACKER_META_KEY], int)]
    for i in reversed(unrelated_indices):
        del torrents[i]

    # fetch threads details
    thread_ids = { str(torrent_dict[RUTRACKER_META_KEY]['thread_id']): torrent_dict for torrent_dict in torrents }
    thread_details = api.get_tor_topic_data(thread_ids.keys())
    for thread_id, torrent_dict in thread_ids.iteritems():
        torrent_dict[RUTRACKER_META_KEY]['thread_details'] = thread_details[thread_id]


torrents = config.torrents_source(*config.torrents_source_args)
torrents_meta = []

for torrent in torrents:
    with open(torrent) as f:
        torrent_dict = bdecode(f.read())
        if RUTRACKER_META_KEY in torrent_dict and isinstance(torrent_dict[RUTRACKER_META_KEY], int):
            # rutracker meta was fetched for this torrent, and it has
            # appeared unrelated to rutracker
            continue
        torrents_meta.append(torrent_dict)

fetch_rutracker_meta(torrents_meta)

#for torrent in torrents_meta:
#    with open('/tmp/test_tor/' + torrent_hash(torrent), 'wb') as f:
#        f.write(bencode(torrent))

# format output for keeper post

forums = { id: {'entries': [], 'size': 0} for id in config.keeped_forums }
for torrent in torrents_meta:
    meta = torrent[RUTRACKER_META_KEY]
    forum_id = meta['thread_details']['forum_id']
    if not meta['thread_details']['forum_id'] in config.keeped_forums:
        continue
    if not qbt.is_torrent_completed(torrent_hash(torrent)):
        continue
    size = torrent_size(torrent)
    forum = forums[forum_id]
    forum['size'] += size
    forum['entries'].append("[*][url={thread_url}]{thread_name}[/url] {torrent_size}".format(
        thread_url='http://rutracker.org/forum/viewtopic.php?t=' + str(meta['thread_id']),
        thread_name=meta['thread_details']['topic_title'],
        torrent_size=pretty_size(size)),
    )

class StreamSplitter:
    def __init__(self, chunk_size):
        self._chunk_size = chunk_size
        self._data_buf = StringIO()
        self._data_len = 0

    def reserve(self, size):
        self._data_len += size

    def print_and_reserve(self, s):
        print s
        self._data_len += len(s) + 1

    def append(self, s):
        if not s.endswith('\n'):
            s += '\n'
        if self._data_len + len(s) < self._chunk_size:
            self._data_buf.write(s)
            self._data_len += len(s)
            return True
        return False

    def dump(self):
        print self._data_buf.getvalue()


for id, forum in forums.iteritems():
    print 'stat for {}'.format(id)
    stream = StreamSplitter(config.report_split_by_size)
    stream.print_and_reserve('[b]Актуально на {}[/b]'.format(datetime.datetime.now().date().isoformat()))
    entries, total_size = forum['entries'], forum['size']
    stream.print_and_reserve('Общее количество хранимых раздач подраздела: {total_cnt} шт. ({total_size})'.format(
        total_cnt=len(entries), total_size=pretty_size(total_size)))

    cur = 0
    approximate_post_entries = 500
    hdr = '[spoiler="Раздачи, взятые на хранение, №№ {start} - {end}"]\n[list=1]'
    ftr = '[/list]\n[/spoiler]\n'
    while cur < len(entries):
        stream.reserve(len(hdr.format(start=cur+1, end=cur+approximate_post_entries)) + len(ftr))
        approximate_post_entries = 0
        while cur + approximate_post_entries < len(entries) and stream.append(entries[cur + approximate_post_entries]):
            approximate_post_entries += 1

        print hdr.format(start=cur+1, end=cur+approximate_post_entries)
        stream.dump()
        print ftr

        stream = StreamSplitter(config.report_split_by_size)
        cur += approximate_post_entries
