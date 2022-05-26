# start a web server to browser the game list
# tornado based web server with support for multiple requests in parallel
# default GET request without special routing serve static file in the webdata directory
# with automatically index.html file in the directory


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

import urllib
import urllib.parse

import tornado
import tornado.ioloop
import tornado.web

import tqdm

ROOT = os.path.dirname(os.path.abspath(__file__))
WEBDATA_DIRECTORY = os.path.join(ROOT, 'webdata')
GAME_ENTRIES_INFO_LIST = []


def make_obj_json_friendly(obj):
    if isinstance(obj, (int, float, str)):
        return obj
    elif isinstance(obj, list):
        return [make_obj_json_friendly(x) for x in obj]
    elif isinstance(obj, dict):
        return {
            make_obj_json_friendly(k): make_obj_json_friendly(v) for k, v in obj.items()
        }
    else:
        return repr(obj)

########################################################################
# static file handler


INVALID_CHARACTER_IN_PATH = ':*?\"<>|'


class InvalidCharacterInPath(Exception):
    pass


def normalize_request_path(request_path: str):
    # un-escaped characters
    unescaped_url = urllib.parse.unquote(request_path)
    # normalize path separators
    normalized_path_sep_url = re.sub(r'[\\/]+', '/', unescaped_url)

    path_components = normalized_path_sep_url.split('/')
    normalized_path_components = []
    for component in path_components:
        if component == '..':
            if len(normalized_path_components) > 0:
                normalized_path_components.pop()
        elif component in ('.', ''):
            pass
        else:
            normalized_path_components.append(component)

    normalized_path = '/'.join(normalized_path_components)
    # check for invalid characters
    for c in INVALID_CHARACTER_IN_PATH:
        if c in normalized_path:
            raise InvalidCharacterInPath(f'invalid character {c} in path')

    return normalized_path


def normalize_local_path_seperator(inpath):
    # windows can still work with forward slash
    return re.sub(r'[\\/]+', '/', inpath)


def is_child_path(parent_path, child_path):
    parent_path = normalize_local_path_seperator(parent_path)
    child_path = normalize_local_path_seperator(child_path)

    # windows hack
    parent_path = parent_path.lower()
    child_path = child_path.lower()

    print('parent_path', parent_path)
    print('child_path', child_path)

    return child_path.startswith(parent_path)


VALID_HTML_INDEX_FILENAME_LIST = [
    'index.html',
    'index.htm',
]


def render_static_directory_listing_html(
    normalized_request_path: str,
    child_filename_list: list,
):
    # black theme css
    html = f'''
<!DOCTYPE html>
<html>
<head>
<title>Directory listing for {normalized_request_path}</title>
<style>
* {{
    background-color: black !important;
    color: white !important;
}}
</style>
</head>
<body>
<h1>Directory listing for {normalized_request_path}</h1>
<ul>
'''
    # TODO render link for each path components
    for child_filename in child_filename_list:
        relative_url = f'./{child_filename}'
        html += f'''
<li><a href="{relative_url}">{child_filename}</a></li>
'''
    html += f'''
</ul>
</body>
</html>
'''
    return html


# 4MB
RESPONSE_FILE_CHUNKS_SIZE = int(4 * 1024 * 1024)


def send_file_data(
    request_handler: tornado.web.RequestHandler,
    inpath: str,
    range_pair_list=None,
):
    with open(inpath, 'rb') as infile:
        if range_pair_list is not None:
            total_number_of_chunks = 0

            for range_pair in range_pair_list:
                remaining_bytes = range_pair[1] - range_pair[0]
                infile.seek(range_pair[0])

                number_of_chunks = int(math.ceil(remaining_bytes / RESPONSE_FILE_CHUNKS_SIZE))
                total_number_of_chunks += number_of_chunks

            pbar = tqdm.tqdm(total=total_number_of_chunks)
            for range_pair in range_pair_list:
                remaining_bytes = range_pair[1] - range_pair[0]
                infile.seek(range_pair[0])

                number_of_chunks = int(math.ceil(remaining_bytes / RESPONSE_FILE_CHUNKS_SIZE))
                for i in range(number_of_chunks):
                    read_data_size = int(min(RESPONSE_FILE_CHUNKS_SIZE, remaining_bytes))
                    data = infile.read(read_data_size)
                    request_handler.write(data)
                    remaining_bytes -= read_data_size

        else:
            # send whole file
            # the content size header and status code should have already been set before calling this function
            filesize = os.stat(inpath).st_size
            number_of_chunks = int(math.ceil(filesize / RESPONSE_FILE_CHUNKS_SIZE))
            pbar = tqdm.tqdm(range(number_of_chunks))
            remote_address = request_handler.request.connection.stream.socket.getpeername()
            description = f'{inpath} > {remote_address}'
            pbar.set_description(description)
            for _ in pbar:
                data = infile.read(RESPONSE_FILE_CHUNKS_SIZE)
                request_handler.write(data)


def handle_webdata_request(
    request_handler: tornado.web.RequestHandler,
):
    request_path = request_handler.request.path
    # normalize request path
    try:
        normalized_request_path = normalize_request_path(request_path)
    except InvalidCharacterInPath as ex:
        print(ex)
        # unauthorize
        request_handler.set_status(403)
        request_handler.set_header('Content-Type', 'application/json')
        response_obj = {
            'message': 'invalid character in path',
            'path': request_path,
        }

        response_str = json.dumps(response_obj)
        request_handler.write(response_str)

        return

    # join with webdata directory
    if len(normalized_request_path) == 0:
        local_path = WEBDATA_DIRECTORY
    elif normalized_request_path == '/':
        local_path = WEBDATA_DIRECTORY
    else:
        local_path = os.path.join(WEBDATA_DIRECTORY, normalized_request_path)

    if local_path == WEBDATA_DIRECTORY:
        pass
    elif not is_child_path(WEBDATA_DIRECTORY, local_path):
        # unauthorize
        request_handler.set_status(403)
        request_handler.set_header('Content-Type', 'application/json')
        response_obj = {
            'message': 'unauthorized access',
            'path': request_path,
        }

        response_str = json.dumps(response_obj)
        request_handler.write(response_str)

        return

    # check if file exists
    if not os.path.exists(local_path):
        # not found
        request_handler.set_status(404)
        request_handler.set_header('Content-Type', 'application/json')
        response_obj = {
            'message': 'file not found',
            'path': request_path,
        }

        response_str = json.dumps(response_obj)
        request_handler.write(response_str)

        return

    file_stat = os.stat(local_path)
    if stat.S_ISDIR(file_stat.st_mode):
        # automatically serve index.html
        # directory
        # check if index.html exists
        child_filename_list = os.listdir(local_path)
        for child_filename in child_filename_list:
            lowered_child_filename = child_filename.lower()
            if lowered_child_filename in VALID_HTML_INDEX_FILENAME_LIST:
                child_filepath = os.path.join(local_path, child_filename)
                # send modified time
                os.path.getmtime(child_filepath)
                # TODO
                request_handler.set_status(200)
                request_handler.set_header('Content-Type', 'text/html')
                filesize = os.stat(child_filepath).st_size
                if filesize > 0:
                    send_file_data(request_handler, child_filepath)
                return

        # not found
        # return directory listing
        # TODO option to disable directory listing
        # contruct static html page
        html_str = render_static_directory_listing_html(
            normalized_request_path,
            child_filename_list,
        )

        request_handler.set_status(200)
        request_handler.set_header('Content-Type', 'text/html')
        request_handler.write(html_str)
        return

    if not stat.S_ISREG(file_stat.st_mode):
        # unauthorize
        # this is not a regular file
        request_handler.set_status(403)
        request_handler.set_header('Content-Type', 'application/json')
        response_obj = {
            'message': 'this is not a regular file',
            'path': request_path,
        }

        response_str = json.dumps(response_obj)
        request_handler.write(response_str)

        return

    # regular file
    # TODO parse and support Range header
    request_handler.set_status(200)
    mime_type = get_mime_type_by_filename(local_path)

    if mime_type in TEXT_MIME_TYPE_LIST:
        # set mime type and charset to utf-8
        header_value = f'{mime_type}; charset=utf-8'
        request_handler.set_header('Content-Type', header_value)
    else:
        request_handler.set_header('Content-Type', mime_type)

    filesize = os.stat(local_path).st_size
    request_handler.set_header('Content-Length', str(filesize))

    send_file_data(request_handler, local_path)


MIME_TYPE_DICT = {
    '.html': 'text/html',
    '.htm': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.mjs': 'application/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
}

TEXT_MIME_TYPE_LIST = [
    'text/html',
    'text/css',
    'text/javascript',
    'application/javascript',
    'application/json',
]


def get_mime_type_by_filename(
    filename: str,
):
    extension = os.path.splitext(filename)[1]
    extension = extension.lower()
    if extension in MIME_TYPE_DICT:
        return MIME_TYPE_DICT[extension]
    else:
        return 'application/octet-stream'
########################################################################

### FETCH GAME LIST DATA API ###########################################


def handle_game_list_request(
    request_handler: tornado.web.RequestHandler,
):
    response_obj = []

    # TODO implement pagination
    total_number_of_games = len(GAME_ENTRIES_INFO_LIST)
    number_of_returned_games = min(20, total_number_of_games)
    for index in tqdm.tqdm(range(number_of_returned_games)):
        game_info = GAME_ENTRIES_INFO_LIST[index]
        if type(game_info) is not dict:
            print(f'warning game_info is not dict - type {type(game_info)} - index {index}')
        else:
            reduced_game_info = {
                'index': index,
            }

            if 'url' not in game_info:
                print(f'warning url not in game_info - index {index}')
            else:
                reduced_game_info['url'] = game_info['url']

            if 'title' not in game_info:
                print(f'warning title not in game_info - index {index}')
            else:
                reduced_game_info['title'] = game_info['title']

            if 'banner_url' not in game_info:
                print(f'warning banner_url not in game_info - index {index}')
            else:
                reduced_game_info['banner_url'] = game_info['banner_url']

            response_obj.append(reduced_game_info)

    print(response_obj)
    response_obj = make_obj_json_friendly(response_obj)
    print(response_obj)
    json_str = json.dumps(response_obj)
    # json_bs = json_str.encode('utf-8')

    request_handler.set_status(200)
    request_handler.set_header('Content-Type', 'application/json, charset=utf-8')
    # request_handler.set_header('Content-Length', str(len(json_bs)))
    # request_handler.write(json_bs)
    request_handler.write(json_str)
    return

########################################################################


class AllRequestHandler(tornado.web.RequestHandler):
    async def get(self):
        try:
            handle_webdata_request(
                request_handler=self,
            )

            return
        except Exception as ex:
            stack_trace_str = traceback.format_exc()
            print(ex)
            print(stack_trace_str)
            response_obj = {
                'message': ex,
                'exception': ex,
                'stack_trace': stack_trace_str,
                'request_handler': self,
            }

            response_obj = make_obj_json_friendly(response_obj)
            response_str = json.dumps(response_obj)
            self.set_status(500)
            self.set_header('Content-Type', 'application/json')
            self.write(response_str)
            return

        # get the request path
        request_url = self.request.path
        self.set_header('Content-Type', 'application/json')
        self.write(repr({
            'request_url': request_url,
        }))

        return
        # DEBUG
        # set header to json
        self.set_header('Content-Type', 'application/json')
        self.write(repr(self.__dict__))
        # TODO

    async def post(self):
        try:
            request_path = self.request.path
            if request_path == '/api/games':
                handle_game_list_request(
                    request_handler=self,
                )

                return
        except Exception as ex:
            stack_trace_str = traceback.format_exc()
            print(ex)
            print(stack_trace_str)
            response_obj = {
                'message': ex,
                'exception': ex,
                'stack_trace': stack_trace_str,
                'request_handler': self,
            }

            response_obj = make_obj_json_friendly(response_obj)
            response_str = json.dumps(response_obj)
            self.set_status(500)
            self.set_header('Content-Type', 'application/json')
            self.write(response_str)
            return

        self.set_header('Content-Type', 'application/json')
        json_friendly_obj = make_obj_json_friendly(self.__dict__)
        json_str = json.dumps(json_friendly_obj)
        self.write(json_str)
        # TODO


def main():
    global GAME_ENTRIES_INFO_LIST

    parser = argparse.ArgumentParser()
    parser.add_argument('port', nargs='?', type=int, default=8888)

    args = parser.parse_args()
    print('args', args)

    port = args.port
    print(f'http://localhost:{port}')

    game_entries_info_log_filepath = 'game_entries.pickle'
    if os.path.exists(game_entries_info_log_filepath):
        with open(game_entries_info_log_filepath, 'rb') as infile:
            GAME_ENTRIES_INFO_LIST = pickle.load(infile)
        print('type(GAME_ENTRIES_INFO_LIST)', type(GAME_ENTRIES_INFO_LIST))
        print('len(GAME_ENTRIES_INFO_LIST)', len(GAME_ENTRIES_INFO_LIST))
    else:
        print(f'warning: {game_entries_info_log_filepath} not found')

    app = tornado.web.Application([
        (r'', AllRequestHandler),
        (r'/', AllRequestHandler),
        (r'/.*', AllRequestHandler),
    ])

    app.listen(port, address='0.0.0.0')
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
