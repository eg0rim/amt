# -*- coding: utf-8 -*-
# amt/network/arxiv.py

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

"""classes for arXiv requests"""

from enum import Enum
from typing import Union, Dict

from PySide6.QtNetwork import QNetworkRequest
from PySide6.QtCore import QUrl
   
class ArxivRequest(QNetworkRequest):
    """class of http requests to arXiv metadata server"""
    baseUrl = "http://export.arxiv.org/api/query"
    def __init__(self, params: Dict['AQP', Union[str,'AQSortBy','AQSortOrder','ASP']] = {}):
        super().__init__(self.baseUrl)
        query = "&".join([f"{key}={value}" for key, value in params.items()])
        if query:
            self.setUrl(QUrl(f"{self.baseUrl}?{query}"))
        else:
            self.setUrl(QUrl(self.baseUrl))
        
    def addParams(self, params: Dict['AQP', Union[str,'AQSortBy','AQSortOrder','ASP']]):
        """add a parameter to the query"""
        url = self.url().toString()
        if url[-6:] == "/query":
            url += "?"
        if not url[-1] == "?":
            url += "&"
        url += "&".join([f"{key}={value}" for key, value in params.items()])
        self.setUrl(QUrl(url))
        
    def addArxivId(self, arxiv_id: str | list[str]):
        """set the arXiv id"""
        if isinstance(arxiv_id, list):
            id = ",".join(arxiv_id)
        else:
            id = arxiv_id
        self.addParams({AQP.ID: id})
    
    def addSearch(self, search: 'ArxivSearchQuery'):
        """set the search query"""
        self.addParams({AQP.SEARCH: str(search)})
        
    def addStart(self, start: int):
        """set the start index"""
        self.addParams({AQP.START: str(start)})
        
    def addMaxResults(self, max_results: int):
        """set the maximum number of results"""
        self.addParams({AQP.MAXRES: str(max_results)})
        
    def addSortBy(self, sort_by: 'AQSortBy'):
        """set the sort by parameter"""
        self.addParams({AQP.SORT_BY: sort_by})
        
    def addSortOrder(self, sort_order: 'AQSortOrder'):
        """set the sort order parameter"""
        self.addParams({AQP.SORT_ORDER: sort_order})
        
class StrEnum(Enum):
    """enum for string values"""
    def __str__(self):
        return self.value
        
class AQP(StrEnum):
    """enum for arXiv query parameters"""
    SEARCH = "search_query"
    ID = "id_list"
    START = "start"
    MAXRES = "max_results"
    SORT_BY = "sortBy"
    SORT_ORDER = "sortOrder"
    
class AQSortBy(StrEnum):
    """enum for arXiv query sort by"""
    REL = "relevance"
    SUB = "submittedDate"
    UPD = "lastUpdatedDate"
    
class AQSortOrder(StrEnum):
    """enum for arXiv query sort order"""
    ASC = "ascending"
    DESC = "descending"

class ASP(StrEnum):
    """enum of arXiv search prefixes"""
    TITLE = "ti"
    AUTHOR = "au"
    ABSTRACT = "abs"
    COMMENT = "co"
    JOURNAL = "jr"
    CATEGORY = "cat"
    REPORT = "rn"
    ID = "id"
    ALL = "all"
    
class ArxivSearchQuery:
    """
    Class of arXiv search query
    For these objects &, | and / operators are overloaded to represent AND, OR and ANDNOT operations
    Due to non-associativity of the operations, one has always explicitly use parentheses to group the operations
    Otherwise, the result may not be as expected
    Methods:
    __init__(self, prefix: str = "", value: str ="", query: str = None)
    __str__(self)
    __and__(self, other: 'ArxivSearchQuery') 
    __or__(self, other: 'ArxivSearchQuery')
    __truediv__(self, other: 'ArxivSearchQuery')
    """
    def __init__(self, prefix: ASP = ASP.ALL, value: str = "", query: str = ""):
        if query:
            self.query = query
        else:
            self.query = f"{prefix.value}:%22{value.replace(' ', '+')}%22" if value else "" 
        
    def __str__(self):
        return self.query
    
    def __and__(self, other: 'ArxivSearchQuery'):
        return ArxivSearchQuery(query=f"%28{self.query}+AND+{other.query}%29")
    
    def __or__(self, other: 'ArxivSearchQuery'):
        return ArxivSearchQuery(query=f"%28{self.query}+OR+{other.query}%29")
    
    def __truediv__(self, other: 'ArxivSearchQuery'):
        return ArxivSearchQuery(query=f"%28{self.query}+ANDNOT+{other.query}%29")
    
    
