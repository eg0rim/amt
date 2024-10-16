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
    def __init__(self, message="Application not specified and default application not found.", fileType:str = None):
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
    - default app might not be able to close the file
    Attributes:
        defaultApp (str): Default external application to open files.
        process (dict[str, str]): process of the opened file.
        alls (dict[str, str]): file extensions and the associated application.
    Methods:
        __init__(self, defaultApp: str = None)
        setDefaultApp(self)
        openFile(self, filePath: str, application: str = None) -> bool
        closeFile(self, filePath: str) -> bool
        fileExists(self, filePath: str) -> bool
    """
    def __init__(self, defaultApp: str = None):
        """ 
        Create an instance of ExternalFileHandler.
        Args:
            defaultApp: Default application to open files.
        """
        super().__init__()
        self.defaultApp: str = None
        self.processes: dict[str,subprocess.Popen] = {}
        self.apps: dict[str,str] = {}
        # perhaps, better to force user to set the apps
        #self.setDefaultApp(defaultApp)
            
    def setDefaultApp(self, app = None):
        """ 
        Set the default application to open files based on the OS.
        """
        if app:
            self.defaultApp = app
            return
        if os.name == 'nt':  # Windows
            self.defaultApp = "start"
        elif os.name == 'posix':  # Unix-like (Linux, macOS, etc.)
            if os.uname().sysname == 'Darwin': # maxOS
                self.defaultApp = "open"
            else:
                self.defaultApp = "xdg-open"
        else:
            self.defaultApp = None

    def setApp(self, fileExt: str, app: str):
        """
        Add an entry to the dictionary of file extensions and associated applications.
        Args:
            fileExt: File extension.
            app: Application to be used to open the file.
        """
        self.apps[fileExt] = app

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
                app = self.apps[ext]
            except KeyError:
                app = self.defaultApp
        if not app:
            logger.error(f"Application not specified for {ext} and default application not found.")
            raise ApplicationNotSetError(fileType=ext)
        try:
            process = subprocess.Popen([app, filePath], stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)
            self.processes[filePath] = process
            return True
        except Exception as e:
            logger.error(f"Failed to open file: {filePath}, Error: {e}")
            return False

    def closeFile(self, filePath: str) -> bool:
        """
        Close the file if the application supports it.
        NOTE: This method is not guaranteed to work for all applications. 
        E.g. it does not work for xdg-open on Linux.
        Args:  
            file_path: Path to the file to be closed.
        Returns:
            True if the file was closed successfully, False otherwise.
        """
        # Implement specific logic to close the file if possible
        if filePath not in self.processes:
            logger.error(f"File not opened: {filePath}")
            return False
        try:
            self.processes[filePath].terminate()
            del self.processes[filePath]
            logger.info(f"Closed file: {filePath}")
            return True
        except Exception as e:
            logger.error(f"Failed to close file: {filePath}, Error: {e}")
            return False
        
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