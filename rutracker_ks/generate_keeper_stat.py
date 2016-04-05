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

for id, forum in forums.iteritems():
    print 'stat for {}'.format(id)
    print '[b]Актуально на {}[/b]'.format(datetime.datetime.now().date().isoformat())
    entries, total_size = forum['entries'], forum['size']
    print 'Общее количество хранимых раздач подраздела: {total_cnt} шт. ({total_size})'.format(
        total_cnt=len(entries), total_size=pretty_size(total_size))
    cur = 0
    while cur < len(entries):
        cur_section_len = min(config.report_split_by, len(entries) - cur)
        print '[spoiler="Раздачи, взятые на хранение, №№ {start} - {end}"]'.format(
            start=cur+1, end=cur+cur_section_len)
        print '[list=1]'
        print '\n'.join(entries[cur : cur + cur_section_len])
        print '[/list]'
        print '[/spoiler]'
        print ''
        cur += cur_section_len
