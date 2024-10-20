# -*- coding: utf-8 -*-
# amt/parser/arxiv.py

# Copyright (c) 2024 Egor Im
# This file is part of Article Management Tool.
# Article Management Tool is free software: you can redistribute it and/or 
# modify it under the terms of the GNU General Public License as published 
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Article Management Tool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""parser for arxiv replies"""

import xml.etree.ElementTree as ET

from amt.logger import getLogger
from amt.db.datamodel import ArticleData, BookData, LecturesData, AuthorData, PublishableData
from PySide6.QtCore import QDateTime, Qt

logger = getLogger(__name__)

# helper functions
def getText( element: ET.Element, tag: str) -> str | None:  
    """
    get text of the first tag child of the element
    Args:
        element (ET.Element): xml element
        tag (str): tag of the element
    Returns:
        str | None: text of the element or None
    """
    elementTag = element.find(tag)
    if elementTag is not None:
        return elementTag.text
    else:
        return None
    
def getAttr( element: ET.Element, tag: str, attr: str) -> str | None:
    """
    get attribute attr of the first tag child of the element
    Args:
        element (ET.Element): xml element
        tag (str): tag of the element
        attr (str): attribute of the element
    Returns:
        str | None: attribute of the element or None
    """
    elementTag = element.find(tag)
    if elementTag is not None:
        return elementTag.get(attr)
    else:
        return None
    
class AMTParser:
    """ 
    Base class for parsing replies from metadata servers.
    Attributes:
        parsedData (list): parsed data
    """
    def __init__(self):
        self.parsedData: list[PublishableData] = []

    def parse(self, data: str) -> tuple[bool, str]:
        """
        Parses data given by string from the metadata server.
        Must be implemented in the derived classes.
        Args:
            data (str): string representation of data from the metadata server
        Returns:
            tuple[bool, str]: success, error message
        """
        raise NotImplementedError

class ArxivParser(AMTParser):
    """
    Class for parsing arxiv api replies
    """
    def __init__(self):
        super().__init__()
    
    def parse(self, xml: str) -> tuple[bool, str]:
        """
        parse xml reply from arxiv
        Args:
            xml (str): xml reply from arxiv
        Returns:    
            tuple[bool, str]: success, error message
        """
        root = ET.fromstring(xml)
        entriesData = []
        entries = root.findall('{http://www.w3.org/2005/Atom}entry')
        for entry in entries:
            # title
            title  = getText(entry, '{http://www.w3.org/2005/Atom}title')
            if title is None:
                logger.error("Title is None")
                continue
            # authors
            title = title.strip().replace("\n", "")
            authors = []
            for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
                if author is None:
                    logger.error("Author is None")
                    continue
                name = getText(author, '{http://www.w3.org/2005/Atom}name')
                authorData = AuthorData(name)
                for affiliation in author.findall('{http://www.w3.org/2005/Atom}arxiv:affiliation'):
                    # TODO: implement several affiliations
                    authorData.affiliation = affiliation.text
                authors.append(AuthorData(name))
            entryData = ArticleData(title, authors)
            # get arxiv id and version
            rawId = getText(entry, '{http://www.w3.org/2005/Atom}id')
            idWVersion = rawId.split("/")[-1]
            # version may not be present
            try:
                id, version = idWVersion.split("v")
                entryData.version = version
            except ValueError:
                id = idWVersion
                entryData.version = "1"
            entryData.arxivid = id
            # links
            # there might be several links 
            # one with rel="related" 
            # two with rel="alternate"and title="pdf" and "doi"
            for link in entry.findall('{http://www.w3.org/2005/Atom}link'):
                if link.get('rel') == "related":
                    entryData.link = link.get('href')
                elif link.get('rel') == "alternate":
                    pass
                    # TODO: implement corresponding columns and fields
                    # if link.get('title') == "pdf":
                    #     entryData.pdfLink = link.get('href')
                    # elif link.get('title') == "doi":
                    #     entryData.doiLink = link.get('href')
            # dates
            datePublished = getText(entry, '{http://www.w3.org/2005/Atom}published')
            entryData.dateArxivUploaded = QDateTime.fromString(datePublished, Qt.ISODate)
            dateUpdated = getText(entry, '{http://www.w3.org/2005/Atom}updated')
            entryData.dateArxivUpdated = QDateTime.fromString(dateUpdated, Qt.ISODate)
            # summary, doi, journal, comment
            summary = getText(entry, '{http://www.w3.org/2005/Atom}summary')
            if summary:
                summary = summary.strip().replace("\n", "")
                entryData.summary = summary
            entryData.doi = getText(entry, '{http://arxiv.org/schemas/atom}doi')
            entryData.journal = getText(entry, '{http://arxiv.org/schemas/atom}journal_ref')
            comment = getText(entry, '{http://arxiv.org/schemas/atom}comment')
            if comment:
                comment = comment.strip().replace("\n", "")
                entryData.comment = comment
            # categories
            entryData.primeCategory = getAttr(entry, '{http://arxiv.org/schemas/atom}primary_category', 'term') 
            for category in entry.findall('{http://arxiv.org/schemas/atom}category'):
                # TODO: all categories
                pass
            entriesData.append(entryData)
        if not entriesData:
            return (False, "No entries found")
        self.parsedData = entriesData
        return (True, "")
            