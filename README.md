# Article Management Tool v0.1.5

Manage articles, books, lecture notes, etc for research.

## Features

Currently this tool supports:
- Storing of research related references.
- Opening entries in an external application.
- Searching within the references.
- Previews.
- Pulling metadata from arxiv.org.
- Searching in arxiv and adding articles directly.
- Downloading pdf-files from arxiv.org.
- Compose bibtex files.

### Soon to be implemented

For the next release v0.2.0:
- Pull metadata from various sources (with the focus on arxiv.org).
- Download and store pdf/djvu/etc files from various sources.
- Compose bibtex files.

## Installing 

### Linux
1. Create a directory where you want Article Management Tool to be installed
```bash
    mkdir /path/to/amt/parent/dir
    cd /path/to/amt/parent/dir
```
2. Clone this repository
```bash
    git clone https://github.com/eg0rim/amt.git
```
3. Execute installation script
```bash
    ./install.sh
```

### Manual
For manual installation:
- Install dependencies from REQUIREMENTS.txt, e.g.
```bash
    pip install -r REQUIREMENTS.txt
```
- Compile ui/qrc files using make
```bash
    make all
```
- `articlemanagementtool.py` serves as an entry point to the application.

## Requirements

This package was tested on 
- `python3.12.3`
- `PySide6>=6.7.3`
- `pymupdf>=1.24.11`

## Changelog

See CHANGELOG.md.

## License

Copyright (c) 2024 Egor Im

This software is licensed under the GNU General Public License v3.0. See the COPYING.txt file for details.
