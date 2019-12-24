# search-fs

A simple python utility that indexes directory and file names in a sqlite database to allow for fast searching.

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

Search any directories for JPG files
```shell script
search-fs --name '*.jpg'
```

Search just one directory for JPG files
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