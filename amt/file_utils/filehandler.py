# -*- coding: utf-8 -*-
# amt/file_utils/filehandler.py

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

"""classes to handle files"""

import os
import subprocess

from amt.db.datamodel import EntryData
from amt.logger import getLogger

logger = getLogger(__name__)

class FileHandler:   
    """
    Abstract class to handle files.
    """     
    def openFile(self):
        """ 
        Abstract method to open a file.
        Must be implemented by the subclass.
        """
        pass
    
    def closeFile(self):
        """ 
        Abstract method to close a file.
        Must be implemented by the subclass.
        """
        pass
    
    def fileExists(self, file : str) -> bool:
        """ 
        Check if the file exists.
        Args:
            file: Path to the file.
        Returns:
            True if the file exists, False otherwise.
        """
        return os.path.isfile(file)

class ApplicationNotSetError(Exception):
    """Exception raised when no application is set for a file type."""
    def __init__(self, message: str ="Application not specified and default application not found.", fileType:str = None):
        """ 
        Create an instance of ApplicationNotSetError.
        Args:
            message (str): Error message.
            fileType (str): File type.
        """ 
        self.fileType = fileType
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.fileType:
            return super().__str__() + f" File type: {self.fileType}"
        else:
            return super().__str__()
        

class ExternalFileHandler(FileHandler):
    """ 
    Class to handle files with external applications. Logic:
    - keep track of the processes of the opened files.
    - filetypes are associated with a particular program
    - the ability to close is not guaranteed
    Attributes:
        defaultApp (str): Default external application to open files.
        _processes (list[tuple[str, subprocess.Popen]]): process of the opened file.
        apps (dict[str, str]): file extensions and the associated application.
    Methods:
        __init__(self, defaultApp: str = None)
        setDefaultApp(self)
        openFile(self, filePath: str, application: str = None) -> bool
        closeFile(self, filePath: str) -> bool
        fileExists(self, filePath: str) -> bool
        setApp(self, fileExt: str, app: str)
        getApps(self) -> dict[str, str]
    """
    def __init__(self, defaultApp: str = ""):
        """ 
        Create an instance of ExternalFileHandler.
        Args:
            defaultApp: Default application to open files.
        """
        super().__init__()
        self._defaultApp: str = ""
        self._processes: tuple[list[str], list[subprocess.Popen]] = ([],[])
        self._apps: dict[str,str] = {}
            
    @property
    def defaultApp(self) -> str:
        return self._defaultApp
    @defaultApp.setter
    def defaultApp(self, app: str):
        """ 
        Set the default application to open files.
        """
        self._defaultApp = app
        # perhaps, better to force user to set the apps
        # if os.name == 'nt':  # Windows
        #     self._defaultApp = "start"
        # elif os.name == 'posix':  # Unix-like (Linux, macOS, etc.)
        #     if os.uname().sysname == 'Darwin': # maxOS
        #         self._defaultApp = "open"
        #     else:
        #         self._defaultApp = "xdg-open"
        # else:
        #     self._defaultApp = None

    def setApp(self, fileExt: str, app: str):
        """
        Add an entry to the dictionary of file extensions and associated applications.
        Args:
            fileExt: File extension.
            app: Application to be used to open the file.
        """
        self._apps[fileExt] = app
        
    @property
    def apps(self) -> dict[str, str]:
        """
        Get the dictionary of file extensions and associated applications.
        Returns:
            Dictionary of file extensions and associated applications.
        """
        return self._apps
    @apps.setter
    def apps(self, apps: dict[str, str]):
        """
        Set the dictionary of file extensions and associated applications.
        Args:
            apps: Dictionary of file extensions and associated applications.
        """
        self._apps = apps
    
    def getOpenedFiles(self) -> list[str]:
        """
        Get the list of opened files.
        Returns:
            List of opened files.
        """
        return self._processes[0]

    def openFile(self, filePath: str, application: str =None) -> bool:
        """
        Open a file using the default or specified application.
        Args:
            file_path: Path to the file to be opened.
            application: Application to be used to open the file.
        Returns:
            True if the file was opened successfully, False otherwise.
        """
        if not self.fileExists(filePath):
            errMsg = f"File does not exist: {filePath}."
            logger.error(errMsg)
            raise FileNotFoundError(errMsg)
        if application:
            app = application
        else:
            try:
                ext = os.path.splitext(filePath)[1][1:]
                logger.debug(f"File extension: {ext}")
                app = self._apps[ext]
            except KeyError:
                app = self._defaultApp
        if not app:
            app = self._defaultApp
        if not app:
            logger.error(f"Application not specified for {ext} and default application not found.")
            raise ApplicationNotSetError(fileType=ext)
        try:
            process = subprocess.Popen([app, filePath], stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)
            if process:
                self._processes[0].append(filePath)
                self._processes[1].append(process)
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Failed to open file: {filePath}, Error: {e}")
            return False

    def closeByIndex(self, index: int) -> bool:
        """
        Close the file by index.
        NOTE: This method is not guaranteed to work for all applications. 
        E.g. it does not work for xdg-open on Linux.
        Args:
            index: Index of the file in the list of opened files.
        Returns:
            True if the file was closed successfully, False otherwise.
        """
        if index >= len(self._processes[0]) or index < 0:
            logger.error(f"Index out of range: {index}")
            return False
        try:
            process = self._processes[1][index]
            file = self._processes[0][index]
            process.terminate()
            self._processes[0].pop(index)
            self._processes[1].pop(index)
            logger.info(f"Closed file: {file} at index: {index}")
            return True
        except Exception as e:
            logger.error(f"Failed to close file: {file} at index: {index}, Error: {e}")
            return False

    def closeFile(self, filePath: str) -> bool:
        """
        Close the file by name.        
        Args:  
            file_path: Path to the file to be closed.
        Returns:
            True if the file was closed successfully, False otherwise.
        """
        # Implement specific logic to close the file if possible
        try:
            index = self._processes[0].index(filePath)
        except ValueError:
            logger.error(f"File not opened: {filePath}")
            return False
        return self.closeByIndex(index)
        
    def closeAllFiles(self):
        """
        Close all opened files.
        """
        for file in self._processes[0][:]:
            self.closeFile(file)
        self._processes = ()
        
    def pollByIndex(self, index: int) -> bool: 
        """
        Check if the file is still open.
        Args:
            index: Index of the file in the list of opened files.
        Returns:
            True if the file is open, False otherwise.
        """
        if index >= len(self._processes[0]) or index < 0:
            logger.error(f"Index out of range: {index}")
            return False
        return self._processes[1][index].poll() is None
        
    def pollFile(self, filePath: str) -> bool:
        """
        Check if the file is still open.
        Args:
            file_path: Path to the file.
        Returns:
            True if the file is open, False otherwise.
        """
        try:
            index = self._processes[0].index(filePath)
        except ValueError:
            logger.error(f"File not opened: {filePath}")
            return False
        return self.pollByIndex(index)
        
    def pollAllFiles(self) -> dict[str, bool]:
        """
        Check if the files are still open.
        Returns:
            Dictionary of file paths and their status.
        """
        return {file: self.pollFile(file) for file in self._processes[0]}
    
    def syncFiles(self):
        """
        Synchronize the file status.
        """
        for file in self._processes[0][:]:
            if not self.pollFile(file):
                i = self._processes[0].index(file)
                self._processes[0].pop(i)
                self._processes[1].pop(i)
    
class ExternalEntryHandler(ExternalFileHandler):
    """ 
    Class to handle entries with external applications.
    Methods:
        __init__(self, defaultApp: str = None)
        openEntry(self, entry: EntryData, application: str = None) -> bool
        closeEntry(self, entry: EntryData) -> bool    
    """
    def __init__(self, defaultApp: str = None):
        super().__init__(defaultApp)

    def openEntry(self, entry: EntryData, application: str = None):
        """ 
        Opens the file associated with the given entry.
        Args:
        entry (EntryData): The entry containing the file information.
        application (str, optional): The application to use for opening the file. Defaults to None.
        Returns:
        bool: True if the file was successfully opened, False otherwise.
        """
        fileName = entry.fileName
        if fileName:
            return self.openFile(fileName, application)
        else:
            errMsg = "Entry does not have associated file."
            logger.error(errMsg)
            raise FileNotFoundError(errMsg)
        
    def closeEntry(self, entry: EntryData):
        """ 
        Close the file associated with the given entry.
        Args:
            entry (EntryData): The entry containing the file information.
        Returns:
            bool: True if the file was successfully closed, False otherwise.
        """
        fileName = entry.fileName
        if fileName:
            return self.closeFile(fileName)
        else:
            logger.error("Entry does not have associated file")
            return False