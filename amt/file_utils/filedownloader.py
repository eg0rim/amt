# -*- coding: utf-8 -*-
# amt/file_utils/filedownloader.py

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

"""classes to download files from the internet"""

from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from amt.logger import getLogger

logger = getLogger(__name__)

class FileDownloader(QObject):
    """ 
    Class to download files from the internet.
    Signals:
        downloadProgressed (int): emitted when the download progress changes; the argument is the percentage of the download progress
        downloadFinished (str): emitted when the download is finished; the argument is the path of the downloaded file
        downloadFailed (str): emitted when the download fails; the argument is the error message
    Attributes:
        manager (QNetworkAccessManager): the network access manager
        destination (str): the path where the file will be saved
        reply (QNetworkReply): the network reply
    Methods:
        downloadFile(url: str, destination: str)
    """
    downloadProgressed = Signal(int)
    downloadFinished = Signal(str)
    downloadFailed = Signal(str)
    def __init__(self, parent=None):
        """ 
        Create a new FileDownloader object.
        Args:
            parent (QObject): the parent object
        """
        super().__init__(parent)
        self.manager: QNetworkAccessManager = QNetworkAccessManager(self)
        self.destination: str = ''        
        self.reply: QNetworkReply = None
        self.manager.finished.connect(self._onFinished)

    def downloadFile(self, url: str, destination: str):
        """ 
        Download a file from the internet.
        Args:
            url (str): the url of the file to download
            destination (str): the path where the file will be saved
        """
        self.destination = destination
        request = QNetworkRequest(QUrl(url))
        self.reply = self.manager.get(request)
        self.reply.downloadProgress.connect(self._onProgress)
        self.reply.finished.connect(self._onFinished)
        self.reply.errorOccurred.connect(self._onError)

    def _onProgress(self, bytes_received: int, bytes_total: int):
        if bytes_total > 0:
            progress = int((bytes_received / bytes_total) * 100)
            self.downloadProgressed.emit(progress)
        else:
            self.downloadProgressed.emit(0)

    def _onFinished(self):
        if not self.reply.error() == QNetworkReply.NoError:
            self.reply.deleteLater()
            return
        try:
            with open(self.destination, 'wb') as file:
                file.write(self.reply.readAll().data())
            self.downloadFinished.emit(self.destination)
        except Exception as e:
            errmsg = f"Failed to write the file at {self.destination}: {str(e)}"
            logger.error(errmsg)
            self.downloadFailed.emit(errmsg)
        self.reply.deleteLater()

    def _onError(self, error: QNetworkReply.NetworkError):
        errmsg = f"Download failed: {self.reply.errorString()}"
        self.downloadFailed.emit(errmsg)
        self.reply.deleteLater()
        logger.error(f"Download failed: {errmsg}")