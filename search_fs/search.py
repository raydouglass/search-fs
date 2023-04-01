import os
import sqlite3
import sys
import argparse
from search_fs import DEFAULT_DB_FILE, DIRECTORY_TYPE, FILE_TYPE
import re

SUFFIXES = ['B', 'KB', 'MB', 'GB', 'TB']
FORMAT_OPTIONS = {'name', 'size', 'created', 'modified'}

def where_clause(ns, conn):
    name = ns.name
    regex = ns.regex
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
    if regex:
        p = re.compile(regex)

        def regex(item):
            return p.match(item) is not None

        queries.append('regex(name)')
        conn.create_function("regex", 1, regex)
    if type and type in ('f', 'd'):
        queries.append('type = ?')
        if type == 'f':
            args.append(FILE_TYPE)
        elif type == 'd':
            args.append(DIRECTORY_TYPE)
    if size is not None:
        prefix, num, suffix = size
        try:
            num = num * (1024 ** SUFFIXES.index(suffix))
        except ValueError:
            print('Unknown suffix for {}'.format(ns.size))
            sys.exit(2)
        if prefix == '+':
            queries.append('size >= ?')
        elif prefix == '-':
            queries.append('size <= ?')
        args.append(num)

    return ' AND '.join(queries), args


def search(ns):
    with sqlite3.connect(ns.database) as conn:
        where, args = where_clause(ns, conn)
        query = 'select parent, name, size, created, modified from files where ' + where
        if ns.debug:
            print('Query=' + query)
            print('Args=' + str(args))
        c = conn.cursor()
        c.execute(query, args)
        for row in c:
            outputs = {
                'name': row[0] + os.sep + row[1],
                'size': str(row[2]),
                'created': row[3],
                'modified': row[4]
            }
            outs = []
            for format_opt in ns.format:
                outs.append(outputs[format_opt])
            yield ' '.join(outs)


def search_and_print(ns):
    end_char = '\0' if ns.zero else '\n'
    for row in search(ns):
        print(row, end=end_char)


def _parse_size(size_str: str):
    pattern = re.compile(r'([+-]?)(\d+(\.\d+)?)([KMGT])?B?')
    m = pattern.match(size_str.upper())
    if not m:
        raise ValueError('Size should be in the form: 1024 (bytes), 500M, -1TB, etc')
    prefix = m.group(1) if m.group(1) else '+'
    size = float(m.group(2))
    suffix = m.group(4) + 'B'
    return prefix, size, suffix


def _parse_format(format: str):
    splits = format.split(',')
    for item in splits:
        if item not in FORMAT_OPTIONS:
            raise ValueError('Format should be a comma separated list of [name, size, created, modified]. Got: '+item)
    return splits

def _get_argparser():
    parser = argparse.ArgumentParser(description='Search the filesystem search index')
    parser.add_argument('--database', '--db', default=DEFAULT_DB_FILE,
                        help='The database file to use. Defaults to {}'.format(DEFAULT_DB_FILE))
    parser.add_argument('--name', '-n', help='Search by name')
    parser.add_argument('--regex', '-r', help='Search by regex on name')
    parser.add_argument('--type', '-t', choices=['f', 'd'], help='Search by type')
    parser.add_argument('--size', '-s', type=_parse_size,
                        help='Search by size. Prepend with + for greater, or - for less.')
    parser.add_argument('-0', dest='zero', action='store_const', const=True, default=False,
                        help='Output results separated by null byte (for xargs -0)')
    parser.add_argument('--strict-dir', '-d', dest='strict_dir', action='store_const', const=True, default=False,
                        help='Match only exact directories instead of walking the tree')
    parser.add_argument('--format', '-f', dest='format', type=_parse_format, default='name',
                        help='Format the output using comma separated list of [name, size, created, modified], defaults to name only')
    parser.add_argument('directories', metavar='dir', nargs='*', help='Which directories to search')

    parser.add_argument('--debug', action='store_const', const=True, default=False,
                        help='Print extra debug information')
    return parser


def main():
    ns = _get_argparser().parse_args()

    if not (ns.name or ns.type or ns.size or ns.regex):
        print('Please specify name/size/type for searching')
        sys.exit(1)
    search_and_print(ns)
