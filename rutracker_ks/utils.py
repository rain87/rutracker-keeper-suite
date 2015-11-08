from bencode import bdecode, bencode
import hashlib
import os
import rutracker_api as api


def scan_folder(folder):
    ret = []
    for root, dirs, files in os.walk(folder):
        ret += [os.path.join(root, f) for f in files
            if f.lower().endswith('.torrent')]
    return ret


def torrent_size(torrent_dict):
    if 'length' in torrent_dict['info']:
        return torrent_dict['info']['length']
    ret = 0
    for file in torrent_dict["info"]["files"]:
        ret += file["length"]
    return ret


def torrent_hash(torrent_dict):
    return hashlib.sha1(bencode(torrent_dict['info'])).hexdigest()


KB = 1000.
MB = 1000 * KB
GB = 1000 * MB
PB = 1000 * GB

def pretty_size(size):
    if size > PB:
        return "{0:.2f} Pb".format(size / PB)
    if size > GB:
        return "{0:.2f} Gb".format(size / GB)
    if size > MB:
        return "{0:.2f} Mb".format(size / MB)
    if size > KB:
        return "{0:.2f} kb".format(size / KB)
    return "{} b".format(size)
