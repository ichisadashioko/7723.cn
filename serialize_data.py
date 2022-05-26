import os
import urllib
import urllib.parse
import time
import re
import hashlib
import traceback
import typing
import pickle

import bs4
from tqdm import tqdm


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


cache_dir = '.requests_cache'
hash_prefix_length = 2


def hash_url(url: str):
    hash_str = hashlib.md5(url.encode('utf-8')).hexdigest()
    hash_str = hash_str.lower()
    return hash_str


def get_hash_file_location(hash_str: str):
    hash_prefix = hash_str[:hash_prefix_length]

    sub_cache_dir = os.path.join(cache_dir, hash_prefix)
    cache_file = os.path.join(sub_cache_dir, hash_str)

    return cache_file, sub_cache_dir


def is_game_page_url(url: str):
    parse_result = urllib.parse.urlparse(url)
    path_parts = parse_result.path.split('/')
    # filter out empty strings
    path_parts = [part for part in path_parts if part]
    if len(path_parts) != 2:
        return False

    if path_parts[0] != 'download':
        return False

    if not path_parts[1].endswith('.htm'):
        return False

    return True


def get_response_from_cache(url: str):
    url_hash = hash_url(url)

    cache_file, sub_cache_dir = get_hash_file_location(url_hash)

    if os.path.exists(cache_file):
        content = open(cache_file, mode='rb').read()
        return content


def parse_game_page_url(url: str):
    if not is_game_page_url(url):
        raise Exception(f'Not a game page url {url}')

    content_bs = get_response_from_cache(url)
    if (content_bs is None) or (len(content_bs) == 0):
        raise Exception(f'Could not get response from cache for {url}')

    _, html_str = Encoding.decode(content_bs)

    game_page_obj = {
        'url': url,
    }

    soup = bs4.BeautifulSoup(html_str)
    ####################################################################
    title_element_list = soup.select('#content .title h3')
    if len(title_element_list) > 1:
        game_name = title_element_list[0].text
        game_page_obj['name'] = game_name
    ####################################################################
    img_element_list = soup.select('#content ul.container img')
    img_url_list = []
    for img_element in img_element_list:
        if 'src' in img_element.attrs:
            img_url_list.append(img_element.attrs['src'])

    if len(img_url_list) > 0:
        game_page_obj['banner_image'] = {
            'url': img_url_list[0],
        }

        gameplay_image_info_list = []
        for img_url in img_url_list:
            gameplay_image_info_list.append({
                'url': img_url,
            })

        game_page_obj['gameplay_image_list'] = gameplay_image_info_list
    ####################################################################
    container_element_list = soup.select('#content ul.container')
    if len(container_element_list) > 2:
        li_element_list = container_element_list[2].select('li')

        game_binary_info_list = []
        for li_element in li_element_list:
            anchor_element = li_element.select_one('a')
            if anchor_element is None:
                continue

            if 'href' not in anchor_element.attrs:
                continue

            download_url = anchor_element.attrs['href']
            game_binary_info = {
                'url': download_url,
            }
            description_element = li_element.select_one('p')
            if description_element is not None:
                description_text = description_element.get_text('\n')
                game_binary_info['description'] = description_text

            game_binary_info_list.append(game_binary_info)

        game_page_obj['binary_info_list'] = game_binary_info_list
    ####################################################################
    return game_page_obj


def get_all_genre_urls(url: str):
    content_bs = get_response_from_cache(url)

    if content_bs is None:
        raise Exception(f'Could not get response from cache for {url}')

    _, content = Encoding.decode(content_bs)
    soup = bs4.BeautifulSoup(content)
    selector = '.pagenation'
    page_container = soup.select_one(selector)

    if page_container is None:
        raise Exception(f'Failed to select {selector} for getting pages container!')

    selector = 'a'
    els = page_container.select(selector)

    if len(els) == 0:
        raise Exception(f'Failed to select {selector} for page navigation anchors!')

    last_page_anchor = els[-1]
    if not 'href' in last_page_anchor.attrs:
        raise Exception(f'The last anchor element does not have href attribute!')

    last_page_url = last_page_anchor.attrs['href']
    genre_base, last_page_doc_name = os.path.split(last_page_url)

    num_sr = re.search(r'\d+', last_page_doc_name)
    if num_sr is None:
        raise Exception(f'Failed to find number of pages!')

    num_text = last_page_doc_name[num_sr.start():num_sr.end()]
    num_pages = int(num_text)

    genre_page_urls = []

    for i in range(num_pages):
        page_url = f'{genre_base}/{last_page_doc_name[:num_sr.start()]}{i+1}{last_page_doc_name[num_sr.end():]}'
        genre_page_urls.append(page_url)

    return genre_page_urls


def parse_game_listing_page(url: str):
    content_bs = get_response_from_cache(url)
    if content_bs is None:
        raise Exception(f'Could not get response from cache for {url}')

    _, decoded_content = Encoding.decode(content_bs)
    soup = bs4.BeautifulSoup(decoded_content)

    selector = '#content'
    content_div = soup.select_one(selector)
    if content_div is None:
        raise Exception(f'Failed to get content container with selector {selector}')

    selector = 'ul.container'
    ul_container = content_div.select_one(selector)
    if ul_container is None:
        raise Exception(f'Failed to get game list container with selector {selector}')

    game_pages = []

    els = ul_container.find_all('li', recursive=False)
    els.extend(ul_container.select('dd>li'))

    for el in els:
        selector = 'a'
        anchor = el.select_one(selector)
        if anchor is None:
            print(f'This game entry does not have an a element!')
            print('->', el)
            print('->', url)
            continue

        if 'href' in anchor.attrs:
            game_page_url = anchor.attrs['href']
            game_pages.append(game_page_url)

    return game_pages


def main():
    genre_first_page_urls = [
        'http://www.7723.cn/zuixin/jiaose_1.htm',  # 角色扮演 # RPG
        'http://www.7723.cn/zuixin/yizhi_1.htm',  # 益智游戏 # Puzzle games
        'http://www.7723.cn/zuixin/dongzuo_1.htm',  # 动作游戏 # Action games
        'http://www.7723.cn/zuixin/saiche_1.htm',  # 赛车游戏 # Racing games
        'http://www.7723.cn/zuixin/maoxian_1.htm',  # 冒险游戏 # Adventure games
        'http://www.7723.cn/zuixin/yangcheng_1.htm',  # 养成游戏 # Dating sim?
        'http://www.7723.cn/zuixin/tiyu_1.htm',  # 体育游戏 # Sports games
        'http://www.7723.cn/zuixin/gedou_1.htm',  # 格斗游戏 # Fighting games
        'http://www.7723.cn/zuixin/qipai_1.htm',  # 棋牌游戏 # Board games
        'http://www.7723.cn/zuixin/celue_1.htm',  # 策略游戏 # Strategy games
        'http://www.7723.cn/zuixin/sheji_1.htm',  # 射击游戏 # Shooting games
        'http://www.7723.cn/zuixin/moni_1.htm',  # 模拟经营 # Simulation (city building, shop management, etc.)
        'http://www.7723.cn/zuixin/feixing_1.htm',  # 飞行游戏 # Flying (e.g. space ship) games
        'http://www.7723.cn/zuixin/wangyou_1.htm',  # 手机网游 # online games
    ]

    game_listing_pages = []

    for first_page_url in tqdm(genre_first_page_urls):
        try:
            genre_page_urls = get_all_genre_urls(first_page_url)
            game_listing_pages.extend(genre_page_urls)
        except Exception as ex:
            print(f'Error when getting genre page url {first_page_url}')
            print(ex)

    pickle_log_filename = f'game_listing_pages-{time.time_ns()}.pickle'
    print(pickle_log_filename)
    with open(pickle_log_filename, 'wb') as outfile:
        pickle.dump(game_listing_pages, outfile)
    ####################################################################
    game_page_url_list = []

    for game_listing_page_url in tqdm(game_listing_pages):
        try:
            game_page_urls = parse_game_listing_page(game_listing_page_url)
            game_page_url_list.extend(game_page_urls)
        except Exception as ex:
            print(f'Error when parsing game listing page {game_listing_page_url}')
            print(ex)

    pickle_log_filename = f'game_page_url_list-{time.time_ns()}.pickle'
    print(pickle_log_filename)
    with open(pickle_log_filename, 'wb') as outfile:
        pickle.dump(game_page_url_list, outfile)
    ####################################################################
    game_page_url_list = list(set(game_page_url_list))

    game_obj_list = []
    for game_page_url in tqdm(game_page_url_list):
        try:
            obj = parse_game_page_url(game_page_url)
            game_obj_list.append(obj)
        except Exception as ex:
            print(f'Error when parsing game page {game_page_url}')
            print(ex)

    pickle_log_filename = f'game_obj_list-{time.time_ns()}.pickle'
    print(pickle_log_filename)
    with open(pickle_log_filename, 'wb') as outfile:
        pickle.dump(game_obj_list, outfile)

    ####################################################################
    image_url_list = []
    game_binary_url_list = []

    for game_obj in tqdm(game_obj_list):
        if 'banner_image' in game_obj:
            image_url_list.append(game_obj['banner_image']['url'])

        if 'gameplay_image_list' in game_obj:
            for gameplay_image in game_obj['gameplay_image_list']:
                image_url_list.append(gameplay_image['url'])

        if 'binary_info_list' in game_obj:
            for binary_info in game_obj['binary_info_list']:
                game_binary_url_list.append(binary_info['url'])

    pickle_log_filename = f'image_url_list-{time.time_ns()}.pickle'
    print(pickle_log_filename)
    with open(pickle_log_filename, 'wb') as outfile:
        pickle.dump(image_url_list, outfile)

    pickle_log_filename = f'game_binary_url_list-{time.time_ns()}.pickle'
    print(pickle_log_filename)
    with open(pickle_log_filename, 'wb') as outfile:
        pickle.dump(game_binary_url_list, outfile)
