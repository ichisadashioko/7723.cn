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

json_config_file = 'webconfig.json'
content_bs = open(json_config_file, 'rb').read()
content_str = content_bs.decode('utf-8')
config_obj = json.loads(content_str)

game_info_list_filepath = config_obj['game_info_list_filepath']
game_binary_url_list_filepath = config_obj['game_binary_url_list_filepath']
image_url_info_dict_filepath = config_obj['image_url_info_dict_filepath']

with open(game_info_list_filepath, 'rb') as infile:
    game_info_list = pickle.load(infile)
with open(game_binary_url_list_filepath, 'rb') as infile:
    game_binary_url_list = pickle.load(infile)
with open(image_url_info_dict_filepath, 'rb') as infile:
    image_url_info_dict = pickle.load(infile)

start_time_ns = time.perf_counter_ns()
game_info_list.sort(key=lambda x: x['name'])
end_time_ns = time.perf_counter_ns()
taken_time_ns = end_time_ns - start_time_ns
print('taken_time_ns', taken_time_ns)
print(f'taken_time_seconds: {(taken_time_ns/10e9):.3f}')
