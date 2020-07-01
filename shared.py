import time
import re
import os
from typing import List, Dict
import hashlib
import traceback

# external modules
from tqdm import tqdm
import requests

cache_dir = '.requests_cache'
hash_prefix_length = 2
default_timeout = 30  # seconds


class TermColor:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'


class Encoding:
    UTF8 = 'utf-8'
    UTF8_WITH_BOM = 'utf-8-sig'
    UTF16 = 'utf-16'
    GB2312 = 'gb2312'
    SHIFT_JIS = 'shift-jis'

    @classmethod
    def decode(cls, bs: bytes):
        try:
            encoding = cls.UTF8_WITH_BOM
            decoded_content = bs.decode(encoding)
            return encoding, decoded_content
        except Exception as ex:
            # traceback.print_exc()
            pass

        try:
            encoding = cls.UTF8
            decoded_content = bs.decode(encoding)
            return encoding, decoded_content
        except Exception as ex:
            # traceback.print_exc()
            pass

        try:
            encoding = cls.UTF16
            decoded_content = bs.decode(encoding)
            return encoding, decoded_content
        except Exception as ex:
            # traceback.print_exc()
            pass

        try:
            encoding = cls.GB2312
            decoded_content = bs.decode(encoding)
            return encoding, decoded_content
        except Exception as ex:
            # traceback.print_exc()
            pass

        try:
            encoding = cls.SHIFT_JIS
            decoded_content = bs.decode(encoding)
            return encoding, decoded_content
        except Exception as ex:
            # traceback.print_exc()
            pass

        return None, bs


def hash_url(url: str):
    hash_str = hashlib.md5(url.encode('utf-8')).hexdigest()
    hash_str = hash_str.lower()
    return hash_str


def get_hash_file_location(hash_str: str):
    hash_prefix = hash_str[:hash_prefix_length]

    sub_cache_dir = os.path.join(cache_dir, hash_prefix)
    cache_file = os.path.join(sub_cache_dir, hash_str)

    return cache_file, sub_cache_dir


def requests_wrapper(url: str, verbose: bool, timeout: int, is_post=False):
    response = None
    error = None
    content = None

    url_hash = hash_url(url)

    cache_file, sub_cache_dir = get_hash_file_location(url_hash)

    if os.path.exists(cache_file):
        if verbose:
            print('Pulling request content from cache!')
            print(url)

        content = open(cache_file, mode='rb').read()

        if len(content) == 0:
            if verbose:
                print('The response was 404!')

            content = None
    else:
        try:
            if is_post:
                response = requests.post(url, timeout=timeout)
            else:
                response = requests.get(url, timeout=timeout)

            if response.ok:
                content = response.content
                if not os.path.exists(sub_cache_dir):
                    os.makedirs(sub_cache_dir)

                try:
                    with open(cache_file, mode='wb') as stream:
                        stream.write(content)
                except Exception as ex:
                    os.remove(cache_file)
                    raise ex

            elif response.status_code == 404:
                # mark the request as successful but empty response
                # so that we don't have to request it again
                open(cache_file, mode='wb').close()
            else:
                print('The response is not usable! Please check the response object! Response status code:', response.status_code)  # noqa
                print('->', url)
        except KeyboardInterrupt as ex:
            raise ex
        except Exception as ex:
            error = ex
            print(f'{TermColor.RED}Failed to request the content!{TermColor.ENDC}')
            print('->', url)
            print(type(ex))
            print(TermColor.RED, end='')
            print(ex)
            print(TermColor.ENDC, end='')
            traceback.print_exc()

    return content, response, error


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
