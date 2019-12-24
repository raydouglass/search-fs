import os
import sys
import sqlite3
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


def walk(input_dirs):
    for input_dir in input_dirs:
        for dir, dirnames, filenames in os.walk(input_dir):
            for filename in filenames:
                path = os.path.join(dir, filename)
                size = os.stat(path, follow_symlinks=False).st_size
                yield path, dir, filename, FILE_TYPE, size
            for dirname in dirnames:
                path = os.path.join(dir, dirname)
                yield path, dir, dirname, DIRECTORY_TYPE, 0


def create_db(db_file, input_dirs):
    print('Indexing {} directories'.format(len(input_dirs)))
    temp_db = db_file + '.temp'
    if os.path.exists(temp_db):
        os.remove(temp_db)
    start = time.time()
    with sqlite3.connect(temp_db) as conn:
        conn.execute(
            'create table files(path text unique not null, parent text not null, name text not null, type integer not null, size integer not null)')
        file_count = 0
        results = walk(input_dirs)
        for split in split_every(10000, results):
            file_count += len(split)
            print('Processed {} files'.format(file_count))
            conn.executemany('insert into files(path, parent, name, type, size) values (?,?,?,?,?)', split)
        conn.execute('create index parent_idx on files(parent)')
        conn.execute('create index name_idx on files(name)')
        conn.execute('create index size_idx on files(size)')
    os.replace(src=temp_db, dst=db_file)
    end = time.time()
    print('Completed in {0:.2f}s'.format(end - start))


def main():
    parser = argparse.ArgumentParser(description='Create the filesystem search index')
    parser.add_argument('--output', '-o', default=DEFAULT_DB_FILE,
                        help='The output database file. Defaults to {}'.format(DEFAULT_DB_FILE))
    parser.add_argument('--dirs', metavar='FILE', help='File containing a list of directories to index')
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
    create_db(ns.output, directories)
