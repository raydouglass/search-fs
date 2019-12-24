import os
import sqlite3
from itertools import islice
import argparse
from search_fs import DEFAULT_DB_FILE, DIRECTORY_TYPE, FILE_TYPE


def split_every(n, iterable):
    i = iter(iterable)
    piece = list(islice(i, n))
    while piece:
        yield piece
        piece = list(islice(i, n))


def walk(input_dir):
    for dir, dirnames, filenames in os.walk(input_dir):
        for filename in filenames:
            path = os.path.join(dir, filename)
            yield path, dir, filename, FILE_TYPE
        for dirname in dirnames:
            path = os.path.join(dir, dirname)
            yield path, dir, dirname, DIRECTORY_TYPE


def create_db(db_file, input_dirs):
    temp_db = db_file + '.temp'
    if os.path.exists(temp_db):
        os.remove(temp_db)
    with sqlite3.connect(temp_db) as conn:
        conn.execute(
            'create table files(path text unique not null, parent text not null, name text not null, type integer not null)')
        file_count = 0
        for input_dir in input_dirs:
            results = walk(input_dir)
            for split in split_every(10000, results):
                file_count += len(split)
                print('Processed {} files'.format(file_count))
                conn.executemany('insert into files(path, parent, name, type) values (?,?,?,?)', split)
        conn.execute('create index parent_idx on files(parent)')
        conn.execute('create index name_idx on files(name)')
    os.replace(src=temp_db, dst=db_file)


def main():
    parser = argparse.ArgumentParser(description='Create the filesystem search index')
    parser.add_argument('--output', '-o', default=DEFAULT_DB_FILE)
    parser.add_argument('directories', metavar='dir', nargs='+')

    ns = parser.parse_args()
    create_db(ns.output, ns.directories)
