# Article Management Tool

Manage articles, books, lecture notes, etc for research.

## Features

- Store research related references.
- Search within the references.

### Soon to be implemented

- Pull metadata from various sources (with the focus on arxiv.org).
- Download and store pdf/djvu/etc files from open sources.
- Compose bibtex files.

## Installing (for Linux)

1. Clone this repository.
2. Create virtual environment and activate (recommended)
```bash
    python3 -m venv /path/to/venv
    source /path/to/venv/bin/activate
```
3. Install (currently, there is an issue with `pyqrdarktheme`, so `--ignore-requires-python` is required; to be resolved in a future release)
```bash
    cd /path/to/article-management-tool
    pip install --ignore-requires-python .
```
2. Compile `.qrc` and `.ui` files
```bash 
    make
```
3. Run the app
```bash
    ./articlemanagementtool.py
```

## Requirements

This package was tested on 
- `python3.12.3`
- `PySide6==6.7.3`
- `pyqtdarktheme==2.1.0`

## License

This software is licensed under the GNU General Public License v3.0. See the COPYING.txt file for details.
