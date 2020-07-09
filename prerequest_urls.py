#!/usr/bin/env python3
# encoding=utf-8
import os
import time
import json
import argparse

from tqdm import tqdm

from shared import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'infile',
        type=str,
        help='JSON file (utf-8) has list of urls',
    )

    args = parser.parse_args()

    infile = args.infile

    url_list = json.load(open(infile, mode='r', encoding='utf-8'))
    not_cached_urls = []

    print(f'{TermColor.BLUE}Filtering cached urls.{TermColor.ENDC}', flush=True)
    pbar = tqdm(url_list)
    for url in pbar:
        url_hash = hash_url(url)
        cache_file, sub_cache_dir = get_hash_file_location(url_hash)

        if os.path.exists(cache_file):
            continue
        else:
            not_cached_urls.append(url)

    if len(not_cached_urls) == 0:
        print(
            f'{TermColor.GREEN}All urls have been cached.{TermColor.ENDC}', flush=True)
    else:
        print(
            f'{TermColor.BLUE}Starting to cache requests...{TermColor.ENDC}', flush=True)
        num_failed_requests = 0
        pbar = tqdm(not_cached_urls)
        for url in pbar:
            url_hash = hash_url(url)
            pbar.set_description(f'{TermColor.BLUE}{infile}{TermColor.ENDC} - {TermColor.RED}{num_failed_requests} failed{TermColor.ENDC} - {url_hash} - {TermColor.GREEN}{url}{TermColor.ENDC}')  # noqa
            content, response, error = GET(url, verbose=False)

            if error is not None:
                num_failed_requests += 1

        print('Number of failed requests:', num_failed_requests)
