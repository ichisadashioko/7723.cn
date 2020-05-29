import os
from tqdm import tqdm

from shared import *

hash_list = os.listdir(cache_dir)

pbar = tqdm(hash_list)
for hash_str in pbar:
    pbar.set_description(hash_str)

    sub_cache_dir = os.path.join(cache_dir, hash_str)
    if not os.path.isdir(sub_cache_dir):
        continue

    cache_filenames = os.listdir(sub_cache_dir)

    for fname in cache_filenames:
        cache_fpath = os.path.join(sub_cache_dir, fname)
        new_cache_fpath = os.path.join(cache_dir, fname)
        os.rename(cache_fpath, new_cache_fpath)

    os.rmdir(sub_cache_dir)