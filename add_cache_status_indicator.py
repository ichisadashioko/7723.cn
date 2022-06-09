import os
import pickle
import posixpath
import argparse
import time
import io
import threading
import json
import re
import stat
import math
import traceback
import gzip
import sys

import urllib
import urllib.parse
import wsgiref.handlers

import tqdm

game_obj_list_filepath = "modified_game_obj_list-1653552476412252800.pickle"
game_binary_url_list_filepath = "tmp_pickle_files/game_binary_url_list-1650280741999342000.pickle"
image_url_info_dict_filepath = "image_url_info_dict-1654534265407578600.pickle"

game_obj_list = pickle.load(open(game_obj_list_filepath, 'rb'))
game_binary_url_list = pickle.load(open(game_binary_url_list_filepath, 'rb'))
image_url_info_dict = pickle.load(open(image_url_info_dict_filepath, 'rb'))

game_info_with_no_images_in_cache_list = []
game_info_with_some_images_in_cache_list = []

for i in tqdm.tqdm(range(len(game_obj_list))):
    has_no_images_in_cache = True
    has_all_images_in_cache = True

    number_of_images_in_cache = 0
    number_of_images = 0

    # banner_image
    if 'banner_image' in game_obj_list[i]:
        if game_obj_list[i]['banner_image'] is not None:
            number_of_images += 1
            url = game_obj_list[i]['banner_image']['url']
            in_cache = (url in image_url_info_dict)
            game_obj_list[i]['banner_image']['in_cache'] = in_cache
            if in_cache:
                has_no_images_in_cache = False
                number_of_images_in_cache += 1
            else:
                has_all_images_in_cache = False

    # gameplay_image_list
    if 'gameplay_image_list' in game_obj_list[i]:
        for gameplay_image in game_obj_list[i]['gameplay_image_list']:
            number_of_images += 1
            url = gameplay_image['url']
            in_cache = (url in image_url_info_dict)
            gameplay_image['in_cache'] = in_cache
            if in_cache:
                number_of_images_in_cache += 1
                has_no_images_in_cache = False
            else:
                has_all_images_in_cache = False

    if has_no_images_in_cache:
        game_info_with_no_images_in_cache_list.append(game_obj_list[i])
    elif not has_all_images_in_cache:
        game_obj_list[i]['number_of_images_note'] = f'{number_of_images_in_cache}/{number_of_images}'
        game_info_with_some_images_in_cache_list.append(game_obj_list[i])

for game_info in game_info_with_some_images_in_cache_list:
    print(game_info['name'], game_info['number_of_images_note'])

log_filepath = f'game_info_list-{time.time_ns()}.pickle'
print(f'log_filepath: {log_filepath}')
with open(log_filepath, 'wb') as outfile:
    pickle.dump(game_obj_list, outfile)

filesize = os.path.getsize(log_filepath)
print(f'{filesize} bytes')
print(f'{(filesize / 1024 / 1024):.02f} MB')

log_filepath = f'game_info_list-{time.time_ns()}.pickle.gzip'
print(f'log_filepath: {log_filepath}')
with gzip.open(log_filepath, 'wb') as outfile:
    pickle.dump(game_obj_list, outfile)

filesize = os.path.getsize(log_filepath)
print(f'{filesize} bytes')
print(f'{(filesize / 1024 / 1024):.02f} MB')
