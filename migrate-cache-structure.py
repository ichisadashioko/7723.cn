#!/usr/bin/env python3
# encoding=utf-8
import os
from tqdm import tqdm

from shared import *

cache_files = os.listdir(cache_dir)

pbar = tqdm(cache_files)
for hash_str in pbar:
    pbar.set_description(f'{TermColor.GREEN}{hash_str}{TermColor.ENDC}')

    cache_filepath = os.path.join(cache_dir, hash_str)

    if os.path.isdir(cache_filepath):
        continue

    new_cache_filepath, sub_cache_dir = get_hash_file_location(hash_str)

    if not os.path.exists(sub_cache_dir):
        os.makedirs(sub_cache_dir)

    os.rename(cache_filepath, new_cache_filepath)
