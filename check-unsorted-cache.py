#!/usr/bin/env python3
# encoding=utf-8
import os
from tqdm import tqdm

from shared import *

child_files = os.listdir(cache_dir)

for child_fname in child_files:
    child_path = os.path.join(cache_dir, child_fname)

    if os.path.isdir(child_path):
        continue

    hash_prefix = child_fname[:hash_prefix_length]
    sub_cache_dir = os.path.join(cache_dir, hash_prefix)
    dest_path = os.path.join(sub_cache_dir, child_fname)

    print(os.path.exists(dest_path), child_fname)
    if os.path.exists(dest_path):
        current_filesize = os.path.getsize(child_path)
        dest_filesize = os.path.getsize(dest_path)
        print((current_filesize == dest_filesize), current_filesize, dest_filesize)  # noqa

        if current_filesize == dest_filesize:
            os.remove(child_path)
