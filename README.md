# search-fs

A simple python utility that indexes directory and file names in a sqlite database to allow for fast searching.

Definitely check out [locate](http://man7.org/linux/man-pages/man1/locate.1.html) before considering this tool.

## Installation

```shell script
pip install search-fs
```

## Usage

```shell script
create-search-fs --help
search-fs --help
```

### Create the database

```shell script
create-search-fs dir1/ dir2/
```

### Search

Search anywhere for JPG files
```shell script
search-fs --name '*.jpg'
```

Search just one directory tree for JPG files
```shell script
search-fs --name '*.jpg' dir1/
```

Search just one directory and not any of the sub directories for JPG files
```shell script
search-fs --name '*.jpg' dir1/ --strict-dir
```

Search for directories
```shell script
search-fs --name 'Directory*' --type d
```

Search for files by size
```shell script
search-fs --size '500M' #Files larger than 500MB
search-fs --size='-10M' #Files smaller than 10MB, Note: make sure you use use '--size=' for less than
```

Search by regular expression
```shell script
search-fs --name '*.jpg' --format=size,name
```

Format the output
```shell script
search-fs --regex '\w+\d\d?\.jpg'
```

### Cron

You can setup a cronjob to run `create-search-fs` so that the index is up to date.

Create `dirs.txt` which contains the directories to index

```
#Lines starting with # are ignored
/path/dir1
/other/dir2
```

Add line with `crontab -e` to update the index every hour

```shell script
0 * * * * /usr/local/bin/create-search-fs --dirs /path/to/dirs.txt
```
