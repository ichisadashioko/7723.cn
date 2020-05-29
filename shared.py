import time
import re
import os
from typing import List, Dict
import hashlib

# external modules
from tqdm import tqdm
import requests

cache_dir = '.requests_cache'
hash_prefix_length = 2
last_response = None
last_exception = None
default_timeout = 30  # seconds


class Encoding:
    UTF8 = 'utf-8'
    UTF8_WITH_BOM = 'utf-8-sig'
    UTF16 = 'utf-16'
    GB2312 = 'gb2312'  # chinese encoding

    @classmethod
    def decode(cls, bs: bytes):
        try:
            return cls.UTF8_WITH_BOM, bs.decode(cls.UTF8_WITH_BOM)
        except Exception as ex:
            # traceback.print_exc()
            pass

        try:
            return cls.UTF8, bs.decode(cls.UTF8)
        except Exception as ex:
            # traceback.print_exc()
            pass

        try:
            return cls.UTF16, bs.decode(cls.UTF16)
        except Exception as ex:
            # traceback.print_exc()
            pass

        try:
            return cls.GB2312, bs.decode(cls.GB2312)
        except Exception as ex:
            # traceback.print_exc()
            pass

        return None, bs


def hash_url(url: str):
    hash_str = hashlib.md5(url.encode('utf-8')).hexdigest()
    hash_str = hash_str.lower()
    return hash_str


def requests_wrapper(url: str, verbose: bool, timeout: int, is_post=False):
    global last_response, last_exception

    last_response = None
    last_exception = None

    url_hash = hash_url(url)
    hash_prefix = url_hash[:hash_prefix_length]

    sub_cache_dir = os.path.join(cache_dir, hash_prefix)
    cache_file = os.path.join(sub_cache_dir, url_hash)

    if os.path.exists(cache_file):
        if verbose:
            print('Pulling request content from cache!')
            print(url)
        content = open(cache_file, mode='rb').read()

        if len(content) == 0:
            if verbose:
                print('The response was 404!')
            return None
        return content
    else:
        try:
            if is_post:
                res = requests.post(url, timeout=timeout)
            else:
                res = requests.get(url, timeout=timeout)

            if res.ok:
                if not os.path.exists(sub_cache_dir):
                    os.makedirs(sub_cache_dir)
                with open(cache_file, mode='wb') as stream:
                    stream.write(res.content)

                return res.content
            elif res.status_code == 404:
                # mark the request as successful but empty response
                # so that we don't have to request it again
                open(cache_file, mode='wb').close()
            else:
                last_response = res
                print('The response is not usable! Please check last_response! Response status code:', res.status_code)  # noqa
                print('->', url)
                return None
        except Exception as ex:
            last_exception = ex
            print('Failed to request the content!')
            print('->', url)
            print(ex)

    return None


def GET(url: str, verbose=True, timeout=default_timeout):
    return requests_wrapper(
        url=url,
        verbose=verbose,
        timeout=timeout,
        is_post=False,
    )


def POST(url: str, verbose=True, timeout=default_timeout):
    return requests_wrapper(
        url=url,
        verbose=verbose,
        timeout=timeout,
        is_post=True,
    )


class GameVersion:
    def __init__(
        self,
        url: str,
        resolution: str,
        model: str,
        description: str,
    ):
        self.url = url
        self.resolution = resolution  # None able
        self.model = model  # None able
        self.description = description  # None able

    def __repr__(self):
        return repr(self.__dict__)


class GameEntry:
    def __init__(
        self,
        url: str,
        title: str,
        banner_url: str,
        sample_gameplay_image_urls: List[str],
        versions: List[GameVersion],
    ):
        self.url = url
        self.title = title  # None able
        self.banner_url = banner_url  # None able
        self.sample_gameplay_image_urls = sample_gameplay_image_urls
        self.versions = versions

    def __repr__(self):
        return repr(self.__dict__)
