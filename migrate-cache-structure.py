import os
from tqdm import tqdm

import * from shared

cache_files = os.listdir(cache_dir)

pbar = tqdm(cache_files)
for hash_str in pbar:
    pbar.set_description(hash_str)

    cache_filepath = os.path.join(cache_dir, hash_str)
    hash_prefix = hash_str[:hash_prefix_length]
    sub_cache_dir = os.path.join(cache_dir, hash_prefix)
    new_cache_filepath = os.path.join(sub_cache_dir, hash_str)

    if not os.path.exists(sub_cache_dir):
        os.makedirs(sub_cache_dir)

    os.rename(cache_filepath, new_cache_filepath)