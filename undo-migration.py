import os
import traceback

from tqdm import tqdm

from shared import *


def find_all_cache_files(fpath: str, pbar=None):
    if pbar is not None:
        pbar.set_description(f'{TermColor.GREEN}{fpath}{TermColor.ENDC}')

    if os.path.isdir(fpath):
        retval = []
        child_files = os.listdir(fpath)

        for child_file in child_files:
            child_fpath = os.path.join(fpath, child_file)
            retval.extend(find_all_cache_files(
                fpath=child_fpath,
                pbar=pbar,
            ))

        return retval
    elif os.path.isfile(fpath):
        return [fpath]
    else:
        return []


def find_all_empty_dirs(fpath: str, pbar=None):
    if pbar is not None:
        pbar.set_description(f'{TermColor.GREEN}{fpath}{TermColor.ENDC}')

    if os.path.isdir(fpath):
        child_files = os.listdir(fpath)

        if len(child_files) == 0:
            return [fpath]
        else:
            retval = []
            for child_file in child_files:
                child_fpath = os.path.join(fpath, child_file)
                retval.extend(find_all_empty_dirs(
                    fpath=child_fpath,
                    pbar=pbar,
                ))

            return retval
    else:
        return []


def remove_empty_dirs(fpath: str):
    pbar = tqdm([fpath])

    empty_dirs = []
    for _fpath in pbar:
        empty_dirs.extend(find_all_empty_dirs(
            fpath=fpath,
            pbar=pbar,
        ))

    pbar = tqdm(empty_dirs)
    for _fpath in pbar:
        pbar.set_description(f'{TermColor.RED}{_fpath}{TermColor.ENDC}')

        try:
            if os.path.isdir(_fpath):
                child_files = os.listdir(_fpath)

                if len(child_files) == 0:
                    os.rmdir(_fpath)
                else:
                    print(f'{TermColor.RED}{_fpath} is not empty!{TermColor.ENDC}', flush=True)  # noqa
            else:
                print(f'{TermColor.RED}{_fpath} is not a directory!{TermColor.ENDC}', flush=True)  # noqa
        except:
            traceback.print_exc()


if __name__ == '__main__':
    cache_filepaths = []

    pbar = tqdm([cache_dir])
    for _fpath in pbar:
        cache_filepaths.extend(find_all_cache_files(
            fpath=_fpath,
            pbar=pbar,
        ))

    print(len(cache_filepaths))

    # pbar = tqdm(cache_filepaths)
    # for fpath in pbar:
    #     pbar.set_description(fpath)

    #     sub_cache_dir = os.path.join(cache_dir, hash_str)
    #     if not os.path.isdir(sub_cache_dir):
    #         continue

    #     cache_filenames = os.listdir(sub_cache_dir)

    #     for fname in cache_filenames:
    #         cache_fpath = os.path.join(sub_cache_dir, fname)
    #         new_cache_fpath = os.path.join(cache_dir, fname)
    #         os.rename(cache_fpath, new_cache_fpath)
