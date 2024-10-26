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

import os, shutil, subprocess, tempfile

from amt.db.datamodel import EntryData, ArticleData, BookData, LecturesData
from amt.db.database import AMTDatabase
from amt.logger import getLogger
from amt.file_utils.path import *

logger = getLogger(__name__)

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
        
class FileHandler:
    """ 
    Abstract base class for file handling.
    
    Methods:
        __init__(self)
        fileExists(file: str) -> bool
        copyFile(src: str, dest: str) -> bool
        moveFile(src: str, dest: str) -> bool
        deleteFile(filePath: str) -> bool
    """
    def __init__(self) -> None:
        super().__init__()
    
    @staticmethod
    def fileExists(file : str) -> bool:
        """ 
        Check if the file exists.
        Args:
            file (str): Path to the file.
        Returns:
            bool: True if the file exists, False otherwise.
        """
        return os.path.isfile(file)
    
    @staticmethod    
    def copyFile(src: str, dest: str) -> bool:
        """
        Copy a file.
        Args:
            src (str): Source file.
            dest (str): Destination file.
        Returns:
            bool: True if the file was copied successfully, False otherwise.
        """
        # copy using shutil
        try:
            shutil.copy2(src, dest)
            logger.info(f"Copied file from {src} to {dest}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy file from {src} to {dest}, Error: {e}")
            return False

    @staticmethod
    def moveFile(src: str, dest: str) -> bool:
        """
        Move a file.
        Args:
            src (str): Source file.
            dest (str): Destination file.
        Returns:
            bool: True if the file was moved successfully, False otherwise.
        """
        # move using shutil
        try:
            shutil.move(src, dest)
            logger.info(f"Moved file from {src} to {dest}")
            return True
        except Exception as e:
            logger.error(f"Failed to move file from {src} to {dest}, Error: {e}")
            return False
    
    @staticmethod
    def deleteFile(filePath: str) -> bool:
        """
        Delete a file.
        Args:
            filePath (str): Path to the file.
        Returns:
            bool: True if the file was deleted successfully, False otherwise.
        """
        try:
            os.remove(filePath)
            logger.info(f"Deleted file: {filePath}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {filePath}, Error: {e}")
            return False
        
class ExternalAppHandler(FileHandler):
    """ 
    Class to handle files with external applications. 
    
    Logic:
    - keep track of the processes of the opened files.
    - filetypes are associated with particular external apps
    - the ability to close is not guaranteed (depends on the external app)
    
    Properties:
        defaultApp (str): Default application to open files.
        apps dict[str, str]: Dictionary of file extensions and associated applications
        
    Methods:
        __init__(self, defaultApp: str = None)
        setApp(self, str, str)
        setApp(self, fileExt: str, app: str)
        openFile(filePath: str) -> bool
        getOpenedFiles(self) -> list[str]
        closeByIndex(self, index: int) -> bool
        closeAllFiles(self)
        pollByIndex(self, index: int) -> bool
        pollAllFiles(self) -> tuple[list[str], list[bool]]
        syncFiles(self)
    """
    def __init__(self, defaultApp: str = ""):
        """ 
        Create an instance of ExternalFileHandler.
        Args:
            defaultApp: Default application to open files.
        """
        super().__init__()
        self._defaultApp: str = defaultApp
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
            logger.debug(f"Opened file: {filePath} with application: {app},  process: {process}, pid: {process.pid}")   
            if process:
                self._processes[0].append(filePath)
                self._processes[1].append(process)
                logger.debug(f"_processes: {self._processes}")
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
        Close the file by path.
        Args:
            filePath: Path to the file.
        Returns:
            True if the file was closed successfully, False otherwise.
        """
        try:
            index = self._processes[0].index(filePath)
            return self.closeByIndex(index)
        except ValueError:
            logger.error(f"File not found in running processes: {filePath}")
            return False
        
    def closeAllFiles(self):
        """
        Close all opened files.
        """
        while len(self._processes[0]) > 0:
            self.closeByIndex(0)
        
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
        
    def pollAllFiles(self) -> tuple[list[str], list[bool]]:
        """
        Check if the files are still open.
        Returns:
            tuple of lists: List of opened files and list of booleans indicating if the files are open.
        """
        ret = ([],[])
        for i in range(len(self._processes[0])):
            poll = self.pollByIndex(i)
            ret[0].append(self._processes[0][i])
            ret[1].append(poll)
        return ret
    
    def syncFiles(self):
        """
        Synchronize the file status.
        """
        newProcesses = ([],[])
        for i in range(len(self._processes[0])):
            if self.pollByIndex(i):
                newProcesses[0].append(self._processes[0][i])
                newProcesses[1].append(self._processes[1][i])
        self._processes = newProcesses
        
class EntryHandler(ExternalAppHandler):
    """ 
    Class to handle entries with external applications.
    Methods:
        __init__(self, defaultApp: str = None)
        openEntry(self, entry: EntryData, application: str = None) -> bool
        closeEntry(self, entry: EntryData) -> bool    
    """    
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
        
    @classmethod
    def moveEntryFile(cls, entry : EntryData, destDir: str) -> bool:
        if entry.fileName:
            newPath = Path(destDir) / entry.fileName
            cls.moveFile(entry.fileName, str(newPath))
            entry.fileName = str(newPath)
            return True
        else:
            logger.error("Entry does not have associated file")
            return False       
        
    @classmethod
    def renameEntryFile(cls, entry: EntryData, newName: str) -> bool:
        if entry.fileName:
            oldPath = entry.fileName
            newPath = Path(oldPath).with_name(newName)
            cls.moveFile(oldPath, str(newPath))
            entry.fileName = str(newPath)
            return True
        else:
            logger.error("Entry does not have associated file")
            return False
                
    @classmethod
    def deleteEntryFile(cls, entry: EntryData) -> bool:
        if entry.fileName:
            fn = entry.fileName
            entry.fileName = None
            return cls.deleteFile(fn)
        else:
            logger.error("Entry does not have associated file")
            return False
                    
                
class DatabaseFileHandler(FileHandler):
    dbDir = DBDIR
    tempDir = TEMPDIR
    os.makedirs(dbDir, exist_ok=True)
    os.makedirs(tempDir, exist_ok=True)
    def __init__(self):
        super().__init__()
        
    @staticmethod
    def openDB(filePath: str) -> AMTDatabase:
        """
        Opens a DB file.
        Args:
            filePath: Path to the new database file.
        Returns:
            AMTDatabase: The new database object.
        """
        db = AMTDatabase(filePath)
        db.open()
        return db
    
    @classmethod
    def openTempDB(cls) -> AMTDatabase:
        """
        Create a temporary database file.
        Returns:
            AMTDatabase: The  temporary database object.
        """
        tmpFile = tempfile.NamedTemporaryFile(delete=False, suffix=".amtdb")   
        tmpFile.close()
        newFile = cls.tempDir / os.path.basename(tmpFile.name)
        cls.moveFile(tmpFile.name, str(newFile))
        db = AMTDatabase(str(newFile))
        db.open()
        return db
    
    @staticmethod
    def closeDB(self, db : AMTDatabase):
        """
        Close the database.
        Args:
            db: The database object to be closed.
        """
        db.close()
        
    @classmethod        
    def saveDBAsAnother(cls, db: AMTDatabase, filePath: str) -> AMTDatabase:
        """ 
        Create a copy of the database and open it.
        Args:
            db: The database object.
            filePath: Path to the new database file.
        Returns:
            AMTDatabase: The new database object.
        """
        oldPath = db.databaseName()
        if db.isOpen():
            db.close()
        cls.copyFile(oldPath, filePath)
        newDB = AMTDatabase(filePath)
        newDB.open()
        return newDB
    
    @classmethod
    def cleanTempDir(cls):
        """
        Clean the temporary directory.
        """
        # delete only .amtdb files
        for file in cls.tempDir.iterdir():
            if file.suffix == ".amtdb":
                filePath = cls.tempDir / file
                cls.deleteFile(str(filePath))

