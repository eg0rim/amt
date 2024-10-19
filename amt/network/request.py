# -*- coding: utf-8 -*-
# amt/network/request.py

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

"""classes for request objects for metadata servers"""

from typing import Union, Dict

from PySide6.QtNetwork import QNetworkRequest
from PySide6.QtCore import QUrl
   
from amt.logger import getLogger
from amt.network.arxiv_aux import *

logger = getLogger(__name__)

class AMTRequest(QNetworkRequest):
    """
    Base class for http requests
    Class Attributes:
        baseUrl (str): base url of the request
    Methods:
        prepareHeaders
    """
    baseUrl = ""
    def __init__(self):
        """ 
        Constructs the request object with predefined base url and prepared headers
        """
        super().__init__(QUrl(self.baseUrl))
        self.prepareHeaders()
        
    def prepareHeaders(self):
        """
        Prepare headers for the request.
        Base class only sets the user agent.
        """
        self.setHeader(QNetworkRequest.UserAgentHeader, "Article Management Tool")

class ArxivRequest(AMTRequest):
    """
    Class of http requests to arXiv metadata server. 
    See https://info.arxiv.org/help/api/user-manual.html for more information.
    Methods:
        prepareHeaders() -> None
        addParams(params: Dict['AQP', Union[str, 'AQSortBy', 'AQSortOrder', 'ArxivSearchQuery']]) -> None
        addArxivId(arxiv_id: Union[str, list[str]]) -> None
        addSearch(search: 'ArxivSearchQuery') -> None
        addStart(start: int) -> None
        addMaxResults(max_results: int) -> None
        addSortBy(sortBy: 'AQSortBy') -> None
        addSortOrder(sortOrder: 'AQSortOrder') -> None
    """
    baseUrl = "http://export.arxiv.org/api/query"
    def __init__(self, params: Dict['AQP', Union[str,'AQSortBy','AQSortOrder','ArxivSearchQuery']] = {}):
        """
        Creates a request with parameters
        Args:
            params (Dict['AQP', Union[str,'AQSortBy','AQSortOrder','ArxivSearchQuery']]): parameters of the request
        """
        super().__init__()
        self.prepareHeaders()
        query = "&".join([f"{key}={value}" for key, value in params.items()])
        if query:
            self.setUrl(QUrl(f"{self.baseUrl}?{query}"))
        else:
            self.setUrl(QUrl(self.baseUrl))
        
    def prepareHeaders(self):
        super().prepareHeaders()
        self.setRawHeader(b"Accept", b"application/atom+xml")
        
    def addParams(self, params: Dict['AQP', Union[str,'AQSortBy','AQSortOrder','ArxivSearchQuery']]):
        """
        Add parameters to the query
        Args:
            params (Dict['AQP', Union[str,'AQSortBy','AQSortOrder','ArxivSearchQuery']]): parameters of the request
        """
        url = self.url().toString()
        if url[-6:] == "/query":
            url += "?"
        if not url[-1] == "?":
            url += "&"
        url += "&".join([f"{key}={value}" for key, value in params.items()])
        self.setUrl(QUrl(url))
        
    def addArxivId(self, arxiv_id: str | list[str]):
        """
        Add arxiv id parameter
        Args:
            arxiv_id (str | list[str]): arxiv id or list of arxiv ids
        """
        if isinstance(arxiv_id, list):
            id = ",".join(arxiv_id)
        else:
            id = arxiv_id
        self.addParams({AQP.ID: id})
    
    def addSearch(self, search: 'ArxivSearchQuery'):
        """
        Add search query parameter
        Args:
            search ('ArxivSearchQuery'): search query
        """
        self.addParams({AQP.SEARCH: search})
        
    def addStart(self, start: int):
        """
        Add the start index parameter
        Args:
            start (int): start index
        """
        self.addParams({AQP.START: str(start)})
        
    def addMaxResults(self, max_results: int):
        """
        Add the max results parameter
        Args:
            max_results (int): max results
        """
        self.addParams({AQP.MAXRES: str(max_results)})
        
    def addSortBy(self, sortBy: 'AQSortBy'):
        """
        Add the sort by parameter
        Args:
            sortBy ('AQSortBy'): sort by parameter
        """
        self.addParams({AQP.SORT_BY: sortBy})
        
    def addSortOrder(self, sortOrder: 'AQSortOrder'):
        """
        Add the sort order parameter
        Args:
            sortOrder ('AQSortOrder'): sort order parameter
        """
        self.addParams({AQP.SORT_ORDER: sortOrder})