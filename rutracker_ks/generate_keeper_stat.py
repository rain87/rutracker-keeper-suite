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

total_size = 0
entries = []
for torrent in torrents_meta:
    meta = torrent[RUTRACKER_META_KEY]
    if not meta['thread_details']['forum_id'] in config.keeped_forums:
        continue
    size = torrent_size(torrent)
    total_size += size
    entries.append("[*][url={thread_url}]{thread_name}[/url] {torrent_size}".format(
        thread_url='http://rutracker.org/forum/viewtopic.php?t=' + str(meta['thread_id']),
        thread_name=meta['thread_details']['topic_title'],
        torrent_size=pretty_size(size)))

print '[spoiler="{total} шт. ({total_size})"]'.format(
    total=len(entries), total_size=pretty_size(total_size))
print '[list=1]'
print '\n'.join(entries)
print '[/list]'
print '[/spoiler]'
