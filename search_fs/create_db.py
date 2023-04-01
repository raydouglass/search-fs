import os
import sys
import sqlite3
from datetime import datetime
from itertools import islice
import argparse
from search_fs import DEFAULT_DB_FILE, DIRECTORY_TYPE, FILE_TYPE
import time


def split_every(n, iterable):
    i = iter(iterable)
    piece = list(islice(i, n))
    while piece:
        yield piece
        piece = list(islice(i, n))

def strip_trailing_slash(dir):
    if dir.endswith(os.sep):
        return dir[:-1]
    else:
        return dir

def walk(input_dirs):
    for input_dir in input_dirs:
        for dir, dirnames, filenames in os.walk(input_dir):
            for filename in filenames:
                path = os.path.join(dir, filename)
                try:
                    stat = os.stat(path, follow_symlinks=False)
                    created_ts = datetime.fromtimestamp(stat.st_ctime)
                    modified_ts = datetime.fromtimestamp(stat.st_mtime)
                    yield strip_trailing_slash(dir), filename, FILE_TYPE, stat.st_size, created_ts, modified_ts
                except FileNotFoundError:
                    pass
            for dirname in dirnames:
                path = os.path.join(dir, dirname)
                stat = os.stat(path, follow_symlinks=False)
                created_ts = datetime.fromtimestamp(stat.st_ctime)
                modified_ts = datetime.fromtimestamp(stat.st_mtime)
                yield strip_trailing_slash(dir), dirname, DIRECTORY_TYPE, None, created_ts, modified_ts


def create_db(db_file, input_dirs, verbose=False):
    if verbose:
        print('Indexing {} directories'.format(len(input_dirs)))
    temp_db = db_file + '.temp'
    if os.path.exists(temp_db):
        os.remove(temp_db)
    start = time.time()
    with sqlite3.connect(temp_db) as conn:
        conn.execute(
            'create table files(parent text not null, name text not null, type integer not null, size integer, created timestamp, modified timestamp)')
        file_count = 0
        results = walk(input_dirs)
        for split in split_every(10000, results):
            file_count += len(split)
            if verbose:
                print('Processed {} files'.format(file_count))
            conn.executemany('insert into files(parent, name, type, size, created, modified) values (?,?,?,?,?,?)', split)
        conn.execute('create index parent_idx on files(parent)')
        conn.execute('create index name_idx on files(name)')
        conn.execute('create index size_idx on files(size)')
        conn.execute('create index created_idx on files(created)')
        conn.execute('create index modified_idx on files(modified)')
    os.replace(src=temp_db, dst=db_file)
    end = time.time()
    if verbose:
        print('Completed in {0:.2f}s'.format(end - start))


def main():
    parser = argparse.ArgumentParser(description='Create the filesystem search index')
    parser.add_argument('--output', '-o', default=DEFAULT_DB_FILE,
                        help='The output database file. Defaults to {}'.format(DEFAULT_DB_FILE))
    parser.add_argument('--dirs', metavar='FILE', help='File containing a list of directories to index')
    parser.add_argument('--verbose', '-v', action='store_const', default=False, const=True, help='Verbose mode')
    parser.add_argument('directories', metavar='dir', nargs='*')

    ns = parser.parse_args()
    directories = ns.directories.copy()
    if ns.dirs:
        with open(ns.dirs) as f:
            for line in f.readlines():
                if line and not line.startswith('#'):
                    directories.append(line.strip())
    if not directories:
        print('You must specify at least one directory to index')
        sys.exit(1)
    else:
        for dir in directories:
            if not os.path.isdir(dir):
                print('Not a directory: {}'.format(dir))
                sys.exit(2)
    create_db(ns.output, directories, ns.verbose)
