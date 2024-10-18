from setuptools import setup, find_packages
from pathlib import Path

thisDirectory = Path(__file__).parent
longDescription = (thisDirectory / "README.md").read_text()

setup(
    name="article-management-tool",
    version="0.1.0",
    author="Egor Im",
    author_email="egor.im.97@gmail.com",
    description="Manage articles, books, lecture notes, etc for research.",
    long_description=longDescription,
    long_description_content_type="text/markdown",
    url="https://github.com/eg0rim/amt",
    packages=find_packages(where="amt"),
    package_dir={"": "amt"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12.3",
    install_requires=[
        "PySide6==6.7.3",
        "pyqtdarktheme==2.1.0",
        "pymupdf==1.24.11"
    ],
    entry_points={
        "console_scripts": [
            "article-management-tool=amt.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)