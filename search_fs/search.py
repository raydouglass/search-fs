import os
import sqlite3
import sys
import argparse
from search_fs import DEFAULT_DB_FILE, DIRECTORY_TYPE, FILE_TYPE

SUFFIXES = ['B', 'KB', 'MB', 'GB', 'TB']


def where_clause(ns):
    name = ns.name
    type = ns.type
    dirs = ns.directories
    strict_dir = ns.strict_dir
    size = ns.size
    args = []
    queries = []
    if dirs:
        if strict_dir:
            dirs = [os.path.abspath(d) for d in dirs]
            parent_query = ' OR '.join('parent = ?' for i in range(len(dirs)))
        else:
            dirs = [os.path.abspath(d) + '%' for d in dirs]
            parent_query = ' OR '.join('parent like ?' for i in range(len(dirs)))
        queries.append('(' + parent_query + ')')
        args.extend(dirs)
    if name:
        name = name.replace('*', '%')
        args.append(name)
        queries.append('name like ?')
    if type and type in ('f', 'd'):
        queries.append('type = ?')
        if type == 'f':
            args.append(FILE_TYPE)
        elif type == 'd':
            args.append(DIRECTORY_TYPE)
    if size is not None:
        size = size.upper()
        if not (size.startswith('+') or size.startswith('-')):
            size = '+' + size
        if not size.endswith('B'):
            size = size + 'B'
        num = float(size[1:-2])
        suffix = size[-2:]
        try:
            num = num * (1024 ** SUFFIXES.index(suffix))
        except ValueError:
            print('Unknown suffix for {}'.format(ns.size))
            sys.exit(2)
        if size.startswith('+'):
            queries.append('size >= ?')
        elif size.startswith('-'):
            queries.append('size <= ?')
        args.append(num)

    return ' AND '.join(queries), args


def search(ns):
    with sqlite3.connect(ns.database) as conn:
        where, args = where_clause(ns)
        query = 'select path from files where ' + where
        c = conn.cursor()
        c.execute(query, args)
        for row in c:
            yield row[0]


def search_and_print(ns):
    end_char = '\0' if ns.zero else '\n'
    for row in search(ns):
        print(row, end=end_char)


def main():
    parser = argparse.ArgumentParser(description='Search the filesystem search index')
    parser.add_argument('--database', '--db', default=DEFAULT_DB_FILE,
                        help='The database file to use. Defaults to {}'.format(DEFAULT_DB_FILE))
    parser.add_argument('--name', '-n', help='Search by name')
    parser.add_argument('--type', '-t', choices=['f', 'd'], help='Search by type')
    parser.add_argument('--size', '-s', help='Search by size. Prepend with + for greater, or - for less.')
    parser.add_argument('-0', dest='zero', action='store_const', const=True, default=False,
                        help='Output results separated by null byte (for xargs -0)')
    parser.add_argument('--strict-dir', '-d', dest='strict_dir', action='store_const', const=True, default=False,
                        help='Match only exact directories instead of walking the tree')
    parser.add_argument('directories', metavar='dir', nargs='*')

    ns = parser.parse_args()

    if not (ns.name or ns.type or ns.size):
        print('Please specify name/size/type for searching')
        sys.exit(1)
    search_and_print(ns)
