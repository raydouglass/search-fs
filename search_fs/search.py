import os
import sqlite3
import sys
import argparse
from search_fs import DEFAULT_DB_FILE, DIRECTORY_TYPE, FILE_TYPE


def _dir_clause(dirs):
    for dir in dirs:
        yield


def where_clause(name, type, dirs, strict_dir):
    args = []
    queries = []
    if dirs:
        if strict_dir:
            dirs = [os.path.abspath(d) for d in dirs]
            parent_query = ' OR '.join('parent = ?' for i in range(len(dirs)))
        else:
            dirs = [os.path.abspath(d)+'%' for d in dirs]
            parent_query = ' OR '.join('parent like ?' for i in range(len(dirs)))
        queries.append('(' + parent_query + ')')
        args.extend(dirs)
    if name:
        name = name.replace('*', '%')
        args.append(name)
        queries.append('name like ?')
    if type:
        queries.append('type = ?')
        if type == 'f':
            args.append(FILE_TYPE)
        elif type == 'd':
            args.append(DIRECTORY_TYPE)
    return ' AND '.join(queries), args


def search(ns):
    end_char = '\0' if ns.zero else '\n'
    with sqlite3.connect(ns.database) as conn:
        where, args = where_clause(ns.name, ns.type, ns.directories, ns.strict_dir)
        query = 'select path from files where ' + where
        c = conn.cursor()
        c.execute(query, args)
        for row in c:
            print(row[0], end=end_char)


def main():
    parser = argparse.ArgumentParser(description='Search the filesystem search index')
    parser.add_argument('--database', '--db', default=DEFAULT_DB_FILE,
                        help='The database file to use. Defaults to {}'.format(DEFAULT_DB_FILE))
    parser.add_argument('--name', '-n', help='Search by name')
    parser.add_argument('--type', '-t', choices=['f', 'd'], help='Search by type')
    parser.add_argument('-0', dest='zero', action='store_const', const=True, default=False,
                        help='Output results separated by null byte (for xargs -0)')
    parser.add_argument('--strict-dir', '-s', dest='strict_dir', action='store_const', const=True, default=False,
                        help='Match only exact directories instead of walking the tree')
    parser.add_argument('directories', metavar='dir', nargs='*')

    ns = parser.parse_args()

    if not (ns.name or ns.type):
        print('Please specify name or type for searching')
        sys.exit(1)
    search(ns)
