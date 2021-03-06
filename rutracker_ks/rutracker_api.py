import requests, urllib
import logging
from time import sleep
import pickle


request_size_limit = 0
LOGGER = logging.getLogger(__name__)

cache = {}

try:
    with open('/tmp/rutracker_cache.pickle', 'rb') as f:
        cache = pickle.load(f)
except Exception:
    pass


def byteify(input):
    if isinstance(input, dict):
        return {byteify(key):byteify(value) for key,value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input


def _reliably_get_data(url):
    for i in range(0, 10):
        r = requests.get(url, headers={'content-type': 'application/json'})
        js = r.json()
        if 'result' in js:
            break
    return byteify(js['result'])


def _get_data(api_name, params={}):
    params_get_string = ''
    for k, v in params.iteritems():
        params_get_string += '{}={}&'.format(k, urllib.quote(v))
    if params_get_string:
        params_get_string = '?' + params_get_string
    return _reliably_get_data('http://api.rutracker.org/v1/' + api_name + params_get_string)


def get_limit():
    try:
        res = _get_data('get_limit')
        request_size_limit = res['limit']
        assert isinstance(request_size_limit, int),\
            'request_size_limit is not int! ({})'.format(request_size_limit)
        return request_size_limit
    except Exception:
        LOGGER.warning('failed to get request_size_limit', exc_info=True)
        return 100


def _iterative_get_data(api_name, full_list, param_generator):
    if not isinstance(full_list, list):
        full_list = [full_list]

    # initialize cache
    """
    global cache
    if not api_name in cache:
        cache[api_name] = {}

    api_cache = cache[api_name]
    # search in cache, first
    cache_keys = set(api_cache.keys())
    cache_hit = cache_keys.intersection(full_list)
    ret = { field: api_cache[field] for field in cache_hit }
    full_list = list(set(full_list) - cache_hit)
    if not full_list:
        return ret
    """

    ret = {}
    current = 0
    while current < len(full_list):
        ret.update(_get_data(api_name, param_generator(
            full_list[current : current + request_size_limit])))
        current += request_size_limit

    """
    # update cache with new data
    api_cache.update(ret)
    with open('/tmp/rutracker_cache.pickle', 'wb') as f:
        pickle.dump(cache, f)
    """

    return ret


def _get_data_by(api_name, filter_name, data):
    response = _iterative_get_data(api_name,
        data,
        lambda data_list: {
            'by': filter_name,
            'val': ','.join(data_list)
        })
    if not isinstance(data, list):
        return response[data]
    return response


get_tor_topic_data = lambda thread_id: _get_data_by('get_tor_topic_data', 'topic_id', thread_id)
get_topic_id = lambda infohash: _get_data_by('get_topic_id', 'hash', infohash)
get_forum_data = lambda forum_id: _get_data_by('get_forum_data', 'forum_id', forum_id)
get_tor_hash = lambda topic_id: _get_data_by('get_tor_hash', 'topic_id', topic_id)
get_forum_torrents_status = lambda id: _reliably_get_data('http://api.rutracker.org/v1/static/pvc/f/{}'.format(id))


def download_torrent(dest_file, keeper_user_id, keeper_api_key, thread, add_retracker=1):
    r = requests.post('http://rutracker.org/forum/dl.php',
        headers={'content-type': 'application/x-www-form-urlencoded'},
        data='keeper_user_id={}&keeper_api_key={}&t={}&add_retracker_url={}'.format(keeper_user_id,
            keeper_api_key, thread, add_retracker))
    for data in r.iter_content(10):
        dest_file.write(data)
    assert 'content-type' in r.headers, 'No content-type provided for {}'.format(thread)
    assert r.headers['content-type'].startswith('application/x-bittorrent'),\
        'Unexpected content-type "{}" for torrent file {}'.format(r.headers['content-type'], thread)


def reliable_download_torrent(dest_file, keeper_user_id, keeper_api_key, thread, add_retracker=1, tries=3):
    for i in range(tries):
        try:
            download_torrent(dest_file, keeper_user_id, keeper_api_key, thread, add_retracker)
            return
        except Exception:
            if i == tries - 1:
                raise
            LOGGER.warning('while downloading {}'.format(thread), exc_info=True)
            sleep(3)
            dest_file.seek(0)


if not request_size_limit:
    request_size_limit = get_limit()
    LOGGER.info('set request_size_limit to %d', request_size_limit)
