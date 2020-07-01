# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import time
import re
import os
import json
from urllib.parse import urlparse, urlunparse, urljoin
from pprint import pprint
import pickle

# external modules
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup

# local modules
from shared import *

# %% [markdown]
# # Crawl all the entry urls from multiple pages from a game genre page.
# %% [markdown]
# We find the `last page` button to parse the number of page for that game genre.
# 
# ![](./docs/images/7723.cn-game-listing-last-page.png)

# %%
def get_all_genre_urls(url: str):
    content, response, error = GET(url)
    
    if content is None:
        return None
    
    _, content = Encoding.decode(content)
    soup = BeautifulSoup(content)
    selector = '.pagenation'
    page_container = soup.select_one(selector)
    
    if page_container is None:
        print(f'Failed to select {selector} for getting pages container!')
        print('->', url)
        return None
    
    selector = 'a'
    els = page_container.select(selector)
    
    if len(els) == 0:
        print(f'Failed to select {selector} for page navigation anchors!')
        print('->', url)
        return None
    
    last_page_anchor = els[-1]
    if not 'href' in last_page_anchor.attrs:
        print(f'The last anchor element does not have href attribute!')
        print('->', url)
        return None

    last_page_url = last_page_anchor.attrs['href']
    genre_base, last_page_doc_name = os.path.split(last_page_url)
    
    num_sr = re.search(r'\d+', last_page_doc_name)
    if num_sr is None:
        print(f'Failed to find number of pages!')
        print('->', url)
        return None
    
    num_text = last_page_doc_name[num_sr.start():num_sr.end()]
    num_pages = int(num_text)
    
    genre_page_urls = []

    for i in range(num_pages):
        page_url = f'{genre_base}/{last_page_doc_name[:num_sr.start()]}{i+1}{last_page_doc_name[num_sr.end():]}'
        genre_page_urls.append(page_url)

    return genre_page_urls

# %% [markdown]
# ![](./docs/images/7723.cn-symbian-hp.png)

# %%
genre_first_page_urls = [
    'http://www.7723.cn/zuixin/jiaose_1.htm', # 角色扮演 # RPG
    'http://www.7723.cn/zuixin/yizhi_1.htm', # 益智游戏 # Puzzle games
    'http://www.7723.cn/zuixin/dongzuo_1.htm', # 动作游戏 # Action games
    'http://www.7723.cn/zuixin/saiche_1.htm', # 赛车游戏 # Racing games
    'http://www.7723.cn/zuixin/maoxian_1.htm', # 冒险游戏 # Adventure games
    'http://www.7723.cn/zuixin/yangcheng_1.htm', # 养成游戏 # Dating sim?
    'http://www.7723.cn/zuixin/tiyu_1.htm', # 体育游戏 # Sports games
    'http://www.7723.cn/zuixin/gedou_1.htm', # 格斗游戏 # Fighting games
    'http://www.7723.cn/zuixin/qipai_1.htm', # 棋牌游戏 # Board games
    'http://www.7723.cn/zuixin/celue_1.htm', # 策略游戏 # Strategy games
    'http://www.7723.cn/zuixin/sheji_1.htm', # 射击游戏 # Shooting games
    'http://www.7723.cn/zuixin/moni_1.htm', # 模拟经营 # Simulation (city building, shop management, etc.)
    'http://www.7723.cn/zuixin/feixing_1.htm', # 飞行游戏 # Flying (e.g. space ship) games
    'http://www.7723.cn/zuixin/wangyou_1.htm', # 手机网游 # online games
]


# %%
# for url in genre_first_page_urls:
#     url_hash = hash_url(url)
#     cache_file, sub_cache_dir = get_hash_file_location(url_hash)

#     print(os.path.exists(cache_file), cache_file)
#     if os.path.exists(cache_file):
#         content = open(cache_file, mode='rb').read()
#         print(type(content), len(content))
        
#         encoding, decoded_content = Encoding.decode(content)
#         print(encoding, type(decoded_content), len(decoded_content))


# %%
game_listing_pages = []

for first_page_url in genre_first_page_urls:
    genre_page_urls = get_all_genre_urls(first_page_url)
    
    if genre_page_urls is None:
        continue

    print(len(genre_page_urls), first_page_url)
    
    game_listing_pages.extend(genre_page_urls)

len(game_listing_pages), len(set(game_listing_pages))

# %% [markdown]
# request and cache response for these pages

# %%
# pbar = tqdm(game_listing_pages)
# for page_url in pbar:
#     pbar.set_description(page_url)
#     GET(page_url, verbose=False)

# %% [markdown]
# # Parse game listing page for game page url
# %% [markdown]
# Here is the sample of game listing page.
# 
# ![](./docs/images/7723.cn-game-listing-page.png)

# %%
def parse_game_listing_page(url: str, verbose=True):
    content, response, error = GET(url, verbose=verbose)
    if content is None:
        if verbose:
            print('content is None!')
        return None
    
    _, decoded_content = Encoding.decode(content)
    soup = BeautifulSoup(decoded_content)
    
    selector = '#content'
    content_div = soup.select_one(selector)
    if content_div is None:
        print(f'Failed to get content container with selector {selector}')
        print('->', url)
        return None
    
    selector = 'ul.container'
    ul_container = content_div.select_one(selector)
    if ul_container is None:
        print(f'Failed to get game list container with selector {selector}')
        print('->', url)
        return None
    
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


# %%
game_pages = []

pbar = tqdm(game_listing_pages)
for url in pbar:
    pbar.set_description(url)
    
    _game_pages = parse_game_listing_page(url, verbose=True)
    
    if _game_pages is None:
        print(f'There is some problem with this page!')
        print('->', url)
        print('='*32)
    else:
        game_pages.extend(_game_pages)


# %%
len(game_pages), len(set(game_pages))

# %% [markdown]
# cache request response while we are doing other things

# %%
# pbar = tqdm(game_pages)
# for url in pbar:
#     pbar.set_description(url)
#     GET(url, verbose=False)

# %% [markdown]
# # Parse game page for title and download link for multiple versions
# %% [markdown]
# Sample game page
# 
# ![]()

# %%
def parse_game_entry_url(url: str, verbose=True):
    content, response, error = GET(url, verbose=verbose)
    
    if content is None:
        print('Please check error from global variables!')
        return None
    
    _, content = Encoding.decode(content)
    soup = BeautifulSoup(content)
    
    selector = '#content'
    content_div = soup.select_one(selector)
    if content_div is None:
        print(f'Format for this page is not compatible! There is no element matches {selector}!')
        print('->', url)
        return None
    
    # retrieve game title
    title = None
    selector = '.title'
    title_div = content_div.select_one(selector)
    if title_div is None:
        print(f'Cannot find title! There is no element matches {selector}!')
        print('->', url)
    else:
        selector = 'h3'
        title_heading = title_div.select_one(selector)
        if title_heading is None:
            print(f'Cannot find title! There is no element matches {selector}!')
            print('->', url)
        else:
            title = title_heading.text
    
    selector = 'ul.container'
    ul_containers = content_div.select('ul.container')
    if not (len(ul_containers) == 3):
        print(f'Format for this page is not compatible! Number of elements match {selector} is not supported!')
        print('->', url)
        return None

    # retrieve game banner
    banner_url = None
    selector = 'img'
    banner_img = ul_containers[0].select_one(selector)
    if banner_img is None:
        print(f'Failed to get game banner with selector {selector}!')
        print('->', url)
    else:
        if 'src' in banner_img.attrs:
            banner_url = banner_img.attrs['src']
        else:
            print(f'Failed to get game banner. The img element does not contain src attribute!')
            print('->', url)
    
    # retrieve sample gameplay images
    sample_gameplay_image_urls = [imgE.attrs['src'] for imgE in ul_containers[1].select('img')]
    
    # retrieve game binaries for multiple phone models
    versions = []
    li_containers = ul_containers[2].select('li')
    versions = []
    for li_container in li_containers:
        selector = 'a'
        anchor_element = li_container.select_one(selector)
        if anchor_element is None:
            print(f'Failed to select anchor with {selector}!')
            print('->', url)
            print('->', li_container)
            continue
        
        if not 'href' in anchor_element.attrs:
            print(f'Failed to retrieve download url. Element does not have href attribute.')
            print('->', url)
            print(anchor_element)
            continue
            
        # send a post request to download the game
        version_url  = anchor_element.attrs['href']
        
        version_resolution = None
        version_model = None
        version_desc = None
        
        selector = 'p'
        version_desc_el = li_container.select_one(selector)
        if version_desc_el is None:
            print(f'Failed to retrieve game version description with {selector} selector!')
            print('->', url)
        else:
            version_desc = version_desc_el.text
            resolution_sr = re.search(r'\((\d+)×(\d+)\)', version_desc)
            
            if resolution_sr is None:
                print(f'Failed to search for this game version screen resolution in description!')
                print('->', url)
                print('->', version_desc)
            else:
                version_resolution = version_desc[resolution_sr.start():resolution_sr.end()]
                version_resolution = version_resolution.replace('×', 'x')
                version_resolution = re.sub(r'[\(\)]+', '', version_resolution)
                
                model_sr = re.search(r'[\x00-\x7F]+', version_desc[:resolution_sr.start()])
                
                if model_sr is None:
                    if '触摸屏通用版' in version_desc:
                        # universal touch screen phone models
                        version_model = 'touch'
                    elif '屏通用版' in version_desc:
                        # universal phone models
                        version_model = 'universal'
                    else:
                        print(f'Failed to search for supported model in description!')
                        print('->', url)
                        print('->', version_desc)
                else:
                    version_model = version_desc[model_sr.start():model_sr.end()]
                    version_model = version_model.replace(' ', '')

        versions.append(GameVersion(
            url=version_url,
            resolution=version_resolution,
            model=version_model,
            description=version_desc,
        ))
    
    return GameEntry(
        url=url,
        title=title,
        banner_url=banner_url,
        sample_gameplay_image_urls=sample_gameplay_image_urls,
        versions=versions,
    )


# %%
game_entries = []
pbar = tqdm(game_pages)
for url in pbar:
    pbar.set_description(f'Parsing {url}')
    
    game_entry = parse_game_entry_url(url, verbose=False)
    
    if game_entry is None:
        continue
    
    game_entries.append(game_entry)


# %%
serialized_game_entries = pickle.dumps(game_entries)
type(serialized_game_entries)


# %%
filename = 'game_entries.pickle'
with open(filename, mode='wb') as stream:
    stream.write(serialized_game_entries)

# game_entries = pickle.loads(open(filename, mode='rb').read())


# %%
pbar = tqdm(game_entries)

url_list = []

for game_entry in pbar:
    if game_entry.banner_url is not None:
        url_list.append(game_entry.banner_url)
#         pbar.set_description(f'{game_entry.url} - {game_entry.banner_url}')
#         GET(game_entry.banner_url, verbose=False)

    for img_url in game_entry.sample_gameplay_image_urls:
        url_list.append(img_url)
#         pbar.set_description(f'{game_entry.url} - {img_url}')
#         GET(img_url, verbose=False)
    
    for game_version in game_entry.versions:
        url_list.append(game_version.url)
#         pbar.set_description(f'{game_entry.url} - {game_version.url}')
#         POST(game_version.url, verbose=False)


# %%
len(url_list)


# %%
# split the url list into multiple list for using with other program to request them
import numpy as np

num_parts = 50
sub_url_lists = np.array_split(np.array(url_list), num_parts)
len(sub_url_lists)


# %%
basename = 'url_list_part_'

for i in range(num_parts):
    print(i, len(sub_url_lists[i]))
    
    filename = basename + repr(i).zfill(len(repr(num_parts)))
    print(filename)
    
    with open(filename, mode='w', encoding='utf-8') as stream:
        json.dump(sub_url_lists[i].tolist(), stream, indent=2)


# %%
# CAUTION: this code might take a few days to complete
# pbar = tqdm(url_list)

# for url in pbar:
#     pbar.set_description(url)
#     GET(url, verbose=False)


# %%
sample_game_urls = [
    'http://www.7723.cn/download/10172.htm', # 战姬无双-花缭乱
    'http://www.7723.cn/download/8077.htm', # 苍穹默示录完美运行版
    'http://www.7723.cn/download/10420.htm', # 苍弓默示录－吞噬时空    
]


# %%
entry_url = 'http://www.7723.cn/download/8077.htm'
entry = parse_game_entry_url(entry_url)
entry

