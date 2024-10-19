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

"""auxillary classes for arXiv requests"""

from enum import Enum

from amt.logger import getLogger

logger = getLogger(__name__)
           
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
    Due to non-associativity of the operations, one has always explicitly use parentheses to group the operations,
    otherwise, the result may not be as expected
    Attributes:
        query (str): search query string
    Methods:
        __init__(self, prefix: str = "", value: str ="", query: str = None)
        __str__(self)
        __and__(self, other: 'ArxivSearchQuery') 
        __or__(self, other: 'ArxivSearchQuery')
        __truediv__(self, other: 'ArxivSearchQuery')
    """
    def __init__(self, prefix: ASP = ASP.ALL, value: str = "", query: str = ""):
        """  
        Crates a new arxiv search string; if no arguments are given, the search string is empty.
        If query is given, it is used as the search string.
        Otherwise, the search string is created from the prefix and value.
        + is used as a space in the value. %22 is used as a quotation mark. %28 and %29 are used as parentheses.
        See https://info.arxiv.org/help/api/user-manual.html for more details.
        Args:
            prefix (ASP): search prefix
            value (str): search value
            query (str): search query
        """
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
    
