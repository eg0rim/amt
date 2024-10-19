# -*- coding: utf-8 -*-
# amt/network/client.py

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

"""classes for clients of metadata servers"""

from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply
from PySide6.QtCore import QObject, Signal
   
from amt.logger import getLogger
from amt.network.parser import ArxivParser
from amt.network.request import ArxivRequest, AMTRequest
from amt.network.arxiv_aux import *

logger = getLogger(__name__)

class AMTClient(QObject):
    """
    Base class for metadata server clients.
    Signals:
        finished (list): signal emitted when the request is finished, contains the parsed data in the form of a list
        errorEncountered: signal emitted when an error is encountered
    """
    finished = Signal(list)
    errorEncountered = Signal(str)
    def __init__(self, parent=None):
        """
        Constructs the client object.
        """
        super().__init__(parent)
        self.manager = QNetworkAccessManager(self)
        self.request: AMTRequest = None
        self.manager.finished.connect(self._onFinished)
        self._error: str | None = None
        
    @property   
    def error(self) -> str | None:
        if self.request is None:
            return "Request is not set"
        return self._error
        
    def parseResponse(self, reply: QNetworkReply) -> list:
        """
        Parses the response of the request.
        Must be implemented in the derived classes.
        Args:
            reply (QNetworkReply): reply object
        Returns:
            list: parsed data
        """
        raise NotImplementedError
        
    def _onFinished(self, reply: QNetworkReply):
        """
        Slot for request finished signal. Parses the response and emits the finished signal.
        """
        if not reply.error() == QNetworkReply.NoError:
            errmsg = f"Error: {reply.error()}: {reply.errorString()}"
            logger.error(errmsg)
            reply.deleteLater()
            self._error = errmsg
            self.errorEncountered.emit(errmsg)
            return 
        parsedData = self.parseResponse(reply)
        self.finished.emit(parsedData)
        reply.deleteLater()
    
    def send(self) -> QNetworkReply | None:
        """
        Sends the request to the server.
        Returns:
            QNetworkReply | None: reply object or None if the request is not set
        """
        logger.debug(f"Sending request: {self.request.url().toString()}")
        logger.debug(f"Request headers: {self.request.rawHeaderList()}")
        self._error = None
        if self.request is None:
            errmsg = "Request is not set"
            logger.error(errmsg)
            self._error = errmsg
            self.errorEncountered.emit(errmsg)
            return None
        return self.manager.get(self.request)

class ArxivClient(AMTClient):
    """
    Class for arXiv api server client.
    """
    def __init__(self, parent=None):
        """
        Constructs the arXiv client object.
        """
        super().__init__(parent)
        self._parser = ArxivParser()
        
    def search(self, query: 'ArxivSearchQuery', start: int = 0, max_results: int = 10, sort_by: AQSortBy = AQSortBy.REL, sort_order: AQSortOrder = AQSortOrder.DESC):
        """
        Prepares the request for searching arXiv metadata.
        Args:
            query ('ArxivSearchQuery'): search query
            start (int): index of the first result
            max_results (int): number of results
            sort_by ('AQSortBy'): sort by parameter
            sort_order ('AQSortOrder'): sort order parameter
        """
        request = ArxivRequest()
        request.addSearch(query)
        request.addStart(start)
        request.addMaxResults(max_results)
        request.addSortBy(sort_by)
        request.addSortOrder(sort_order)
        self.request = request
        
    def getById(self, arxiv_id: str | list[str]):
        """
        Prepares request for getting metadata by arXiv id.
        Args:
            arxiv_id (str | list[str]): arXiv id or list of arXiv ids
        """
        request = ArxivRequest()
        request.addArxivId(arxiv_id)
        self.request = request
        
    def parseResponse(self, reply: QNetworkReply) -> list:
        xmlReply = reply.readAll().data().decode()
        status, msg = self._parser.parse(xmlReply)
        if status:
            self._error = None
            return self._parser.parsedData[:]
        else:
            errmsg = f"Error: {msg}"
            self._error = errmsg
            logger.error(errmsg)
            self.errorEncountered.emit(errmsg)
            return []
        