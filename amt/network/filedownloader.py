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
from pathlib import Path 
import os, re

from amt.logger import getLogger
from amt.db.datamodel import PublishableData, ArticleData, BookData, LecturesData  
from amt.file_utils.path import DEFAULTDIR, DOWNLOADDIR

logger = getLogger(__name__)

class FileDownloader(QObject):
    """ 
    Class to download files from the internet.
    Signals:
        downloadProgressed (int, int, int): emitted when the download progress changes; the arguments are: current download file number, total number of files, progress in percent
        downloadFinished (list[str]): emitted when the download is finished, even if fails occured; the argument is the list of downloaded files, can be empty
        downloadFailed (str): emitted when a download fails; the argument is the error message
        downloadFinishedWithErrors (list[str]): emitted when the download is finished with errors; the argument is the list of error messages
    Attributes:
        downloadQueue (dict[str, str]): the download queue; keys are the destination paths, values are the urls
        downloadedFiles (list[str]): the list of downloaded files
    Methods:
        addDownloadFile(url: str, destination: str)
        startDownload
        downloadFile(url: str, destination: str)
    """
    downloadProgressed = Signal(int, int, int)
    downloadFinished = Signal(list) # list of downloaded files
    downloadFinishedWithErrors = Signal(list) # list of errors
    downloadFailed = Signal(str)
    def __init__(self, parent=None):
        """ 
        Create a new FileDownloader object.
        Args:
            parent (QObject): the parent object
        """
        super().__init__(parent)
        # attributes
        self.downloadQueue: dict[str, str] = {}  
        self.downloadedFiles: list[str] = []
        # private attributes
        self._manager: QNetworkAccessManager = QNetworkAccessManager(self)
        self._totalNumberOfFiles = 0
        self._currentFileNumber = 0    
        self._reply: QNetworkReply = None
        self._downloadInProgress = False
        self._singleFileDestination: str = None
        self._errors: list[str] = []
        # connect signals
        self._manager.finished.connect(self._continueDownload)
        self.downloadFinished.connect(logger.debug("Download finished"))
        self.downloadProgressed.connect(lambda a,b,c: logger.debug(f"Download progress changed: {a}/{b} {c}%"))
       
        self.downloadFailed.connect(self._addError)
        
    def _addError(self, error: str):
        self._errors.append(error)
        
    def _getCurrentUrl(self):
        return list(self.downloadQueue.values())[self._currentFileNumber]
    
    def _getCurrentDestination(self):  
        return list(self.downloadQueue.keys())[self._currentFileNumber]

    def addDownloadFile(self, url: str, destination: str) -> bool:
        """ 
        Adds a file to the download queue
        Args:
            url (str): the url of the file to download
            destination (str): the path where the file will be saved
        Returns: 
            bool: True, if adding is succesfull
        """
        logger.debug(f"Adding file to download queue: {url} to {destination}")
        if self._downloadInProgress:
            logger.error("Could not add to the queue: the download is in progress")
            return False
        if destination in self.downloadQueue.keys():
            logger.warning("Destination is already set; replacing it...")
        self.downloadQueue[destination] = url
        logger.debug(f"Added file to download queue: {url} to {destination}")
        return True
    
    def downloadFile(self, url: str, destination: str):
        """ 
        Downloads a single file right away
        """
        self._downloadInProgress = True
        self.downloadedFiles = []
        logger.debug(f"Starting download single file: {url} to {destination}")
        self._singleFileDestination = destination
        request = QNetworkRequest(QUrl(url))
        self._reply = self._manager.get(request)
        self._reply.downloadProgress.connect(self._onProgress)
        self._reply.errorOccurred.connect(self._onError)
        
    def startDownload(self):
        """ 
        Starts downloading the files in the download queue
        """
        self._downloadInProgress = True
        self.downloadedFiles = []
        logger.debug(f"Starting download of {len(self.downloadQueue)} files")
        logger.debug(f"Download queue: {self.downloadQueue}")
        self._totalNumberOfFiles = len(self.downloadQueue)
        if self._totalNumberOfFiles < 1:
            logger.error(f"Download queue is empty")
            return
        self._currentFileNumber = 0
        url = self._getCurrentUrl()
        logger.debug(f"Downloading file from {url} to {self._getCurrentDestination()}")
        request = QNetworkRequest(QUrl(url))
        self._reply = self._manager.get(request)
        self._reply.downloadProgress.connect(self._onProgress)
        self._reply.errorOccurred.connect(self._onError)

    def _onProgress(self, bytes_received: int, bytes_total: int):    
        if bytes_total > 0:
            progress = (bytes_received / bytes_total)
            if self._singleFileDestination is None:
                totalProgress = int((self._currentFileNumber + progress) / self._totalNumberOfFiles * 100)
                self.downloadProgressed.emit(self._currentFileNumber + 1, self._totalNumberOfFiles, totalProgress)
            else:
                self.downloadProgressed.emit(1, 1, int(progress*100))
        else:
            self.downloadProgressed.emit(0, 0, 0)
            
    def _continueDownload(self):
        if self._reply.error() == QNetworkReply.NoError:
            # write file
            if self._singleFileDestination:
                destination = self._singleFileDestination
            else:
                destination = self._getCurrentDestination()
            try:
                with open(destination, 'wb') as file:
                    file.write(self._reply.readAll().data())
                self.downloadedFiles.append(destination)
                logger.debug(f"Downloaded file to {destination}")
            except Exception as e:
                errmsg = f"Failed to write the file at {destination}: {str(e)}"
                logger.error(errmsg)
                self.downloadFailed.emit(errmsg)
            self._reply.deleteLater()
        if self._singleFileDestination:
            self.downloadFinished.emit(self.downloadedFiles)
            if self._errors:
                self.downloadFinishedWithErrors.emit(self._errors)
            self._downloadInProgress = False
            self._singleFileDestination = None
            return        
        if self._currentFileNumber == self._totalNumberOfFiles - 1:
            logger.debug("Download finished")
            self.downloadFinished.emit(self.downloadedFiles)
            if self._errors:
                self.downloadFinishedWithErrors.emit(self._errors)
            self.downloadQueue = {}
            self._downloadInProgress = False
            return
        self._currentFileNumber += 1
        url = self._getCurrentUrl()
        logger.debug(f"Downloading file from {url} to {list(self.downloadQueue.keys())[self._currentFileNumber]}")
        request = QNetworkRequest(QUrl(url))
        self._reply = self._manager.get(request)
        self._reply.downloadProgress.connect(self._onProgress)
        self._reply.errorOccurred.connect(self._onError)

    def _onError(self, error: QNetworkReply.NetworkError):
        currentUrl = self._getCurrentUrl()
        errmsg = f"Download failed from {currentUrl}: {self._reply.errorString()}"
        self.downloadFailed.emit(errmsg)
        logger.error(f"{errmsg}")
        self._reply.deleteLater()
        
class EntryDownloader(FileDownloader):
    """ 
    Class to download entries. The download directory is determined by the entry's title.
    """
    downloadDirectory = DOWNLOADDIR
    entryDirectories = {ArticleData: downloadDirectory/"Articles", BookData: downloadDirectory/"Books", LecturesData: downloadDirectory/"Lectures"}
    def __init__(self, parent=None):
        super().__init__(parent)
        # create download directory if it does not exist
        os.makedirs(self.downloadDirectory, exist_ok=True)
        for directory in self.entryDirectories.values():
            os.makedirs(directory, exist_ok=True)
        self.entries: dict[str, 'PublishableData'] = {}
        self.singleEntry: PublishableData = None
        self.downloadFinished.connect(self.addFilesToEntry)
    
    @staticmethod    
    def generateFileName(entry: PublishableData) -> str:
        pattern = r'[^a-zA-Z0-9\-_.]'
        return re.sub(pattern, '', re.sub(' ', '_', entry.toString()))
        
    def addDownloadEntry(self, entry: PublishableData) -> bool:
        url = entry.filelink
        fn = self.generateFileName(entry)
        # TODO: fix extension
        # TODO: fix too long file names
        destination = str(self.entryDirectories[entry.__class__] / f"{fn}.pdf")
        if not url:
            errmsg = f"Entry {entry.title} has no file link"
            logger.error(errmsg)
            return False
        self.entries[destination] = entry
        return super().addDownloadFile(url, destination)
    
    def downloadEntry(self, entry: PublishableData):
        url = entry.filelink
        fn = self.generateFileName(entry)
        destination = str(self.entryDirectories[entry.__class__] / f"{fn}.pdf")
        if not url:
            errmsg = f"Entry {entry.title} has no file link"
            logger.error(errmsg)
            return False
        self.singleEntry = entry
        return super().downloadFile(url, destination)
        
    def addFilesToEntry(self, files: list[str]):
        if self.singleEntry:
            if len(files) != 1:
                logger.error("Single entry download failed")
                return
            self.singleEntry.fileName = files[0]
        else:
            for file in files:
                self.entries[file].fileName = file
        self.singleEntry = None
        self.entries = []