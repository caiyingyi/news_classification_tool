# -*- coding:utf-8 -*-
import re
import random
import socket
import struct
import binascii
from random import randint
from bs4 import BeautifulSoup
import grequests
import hashlib
from urlparse import urlparse
import logging
import redis
from scrapy.utils.project import get_project_settings

logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)


class Helper(object):

    @staticmethod
    def random_ip():
        return socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))

    @staticmethod
    def parse_images(html_doc, attr='src'):
        soup = BeautifulSoup(html_doc, 'lxml')
        return [x.get(attr) for x in soup.find_all('img') if x and x.get(attr)]

    @staticmethod
    def parse_toutiao_videos(html_doc):
        p = re.compile(r'tt-videoid=[\'"](?P<id>\w+?)[\'"]')
        result = p.search(html_doc)
        if not result:
            return []

        return list(set(p.findall(html_doc)))

    @staticmethod
    def toutiao_video(video_id):
        url = 'http://i.snssdk.com'
        r = '/video/urls/v/1/toutiao/mp4/' + \
            str(video_id) + '?r=' + \
            ''.join([str(randint(1, 9))] + [str(randint(0, 9))
                                            for p in range(1, 16)])
        s = (binascii.crc32(r) & (2**32 - 1)) >> 0
        return ''.join([url, r, '&s=', str(s)])

    @staticmethod
    def cdn_images(urls):
        rs = []
        for (k,v) in urls.items():
            hostname = urlparse(k).hostname
            path = urlparse(k).path
            query = urlparse(k).query

            key = ''.join([str(hashlib.md5(hostname).hexdigest())[:8], '/', hashlib.md5(k).hexdigest()])
            urls[k] = ''.join(['http://p.cdn.sohu.com/', key])

            url = ''.join(['http://bjcnc.scs-in.sohucs.com/storage', path])
            if query:
                url = ''.join([url, '?', query])

            rs.append(
                grequests.head(url, headers={
                    'x-scs-meta-mirror-host': hostname,
                    'x-scs-meta-upload-key': key
                })
            )
        grequests.map(rs)

        return urls

    @staticmethod
    def replace_words(text, word_dic):
        yo = re.compile('|'.join(map(re.escape, word_dic)))

        def translate(mat):
            return word_dic[mat.group(0)]

        return yo.sub(translate, text)


class Singleton(object):
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
        return cls._instance


class CheckRepeat(Singleton):

    site_id = 0
    redis = None

    def __init__(self, site_id, redis_server=None):
        self.site_id = site_id
        self.key = 'check:repeat:%s' % self.site_id
        if redis_server is not None:
            self.redis = redis_server
        elif self.redis:
            pass
        else:
            # self.redis = redis.from_url('redis://:spideredis@10.16.39.169:7800')
            redis_url = get_project_settings().get('DUPLICATE_REDIS_URL', 'redis://:spideredis@10.11.161.94:7800')
            # redis_url = 'redis://:spideredis@10.11.161.94:7800'
            self.redis = redis.from_url(redis_url, max_connections=100)

    def exist(self, item_id):
        return self.redis.sismember(self.key, item_id)

    def add(self, item_id):
        return self.redis.sadd(self.key, item_id)


class CheckSightRepeat(object):
    site_id = 0

    def __init__(self, site_id):
        self.site_id = site_id
        self.key = 'check:sight:repeat:%s' % self.site_id
        self.redis = redis.from_url('redis://:spideredis@10.16.39.169:7800')
        pass

    def exist(self, item_id):
        return self.redis.sismember(self.key, item_id)

    def add(self, item_id):
        return self.redis.sadd(self.key, item_id)


class CheckLastItem(object):
    site_id = 0

    def __init__(self, site_id):
        self.site_id = site_id
        self.key = 'check:last:item:%s' % self.site_id
        self.redis = redis.from_url('redis://:spideredis@10.16.39.169:7800')
        pass

    def get_last_item(self, media_id=0):
        return self.redis.hget(self.key, media_id)

    def set_last_item(self, item_id, media_id=0):
        self.redis.hset(self.key, media_id, item_id)


class CheckLastStartTime(object):
    site_id = 0

    def __init__(self, site_id):
        self.site_id = site_id
        self.key = 'last:start:time:%s' % self.site_id
        self.redis = redis.from_url('redis://:spideredis@10.16.39.169:7800')
        pass

    def get_last_time(self, media_id=0):
        return self.redis.hget(self.key, media_id)

    def set_last_time(self, start_time, media_id=0):
        self.redis.hset(self.key, media_id, start_time)


class CrawlQueue(Singleton):

    redis = None

    def __init__(self, redis_server=None):
        if redis_server is not None:
            self.redis = redis_server
        elif self.redis:
            pass
        else:
            redis_url = get_project_settings().get('REDIS_URL', 'redis://:spideredis@10.16.39.169:7800')
            self.redis = redis.from_url(redis_url, max_connections=100)

    def put_queue_set(self, key, value):
        return self.redis.sadd(key, value)

    def put_queue_list(self, key, value):
        return self.redis.rpush(key, value)
