import requests, urllib
import logging


request_size_limit = 0
LOGGER = logging.getLogger(__name__)


def _get_data(api_name, params={}):
    def byteify(input):
        if isinstance(input, dict):
            return {byteify(key):byteify(value) for key,value in input.iteritems()}
        elif isinstance(input, list):
            return [byteify(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input

    params_get_string = ''
    for k, v in params.iteritems():
        params_get_string += '{}={}&'.format(k, urllib.quote(v))
    if params_get_string:
        params_get_string = '?' + params_get_string
    r = requests.get('http://api.rutracker.org/v1/' + api_name + params_get_string,
        headers={'content-type': 'application/json'})
    return byteify(r.json()['result'])


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
    current = 0
    ret = {}
    while current < len(full_list):
        ret.update(_get_data(api_name, param_generator(
            full_list[current : current + request_size_limit])))
        current += request_size_limit
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


if not request_size_limit:
    request_size_limit = get_limit()
    LOGGER.info('set request_size_limit to %d', request_size_limit)
