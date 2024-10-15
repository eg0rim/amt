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

class ExternalFileHandler(FileHandler):
    """ 
    CSlass to externally handle files.
    Attributes:
        defaultApp: Default external application to open files.
        process: process of the opened file.
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
        if defaultApp:
            self.defaultApp = defaultApp
        else:
            self.setDefaultApp()
            
    def setDefaultApp(self):
        """ 
        Set the default application to open files based on the OS.
        """
        if os.name == 'nt':  # Windows
            self.defaultApp = "start"
        elif os.name == 'posix':  # Unix-like (Linux, macOS, etc.)
            if os.uname().sysname == 'Darwin': # maxOS
                self.defaultApp = "open"
            else:
                self.defaultApp = "xdg-open"
        else:
            self.defaultApp = None

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
            logger.error(f"File does not exist: {filePath}")
            return False
        if application:
            app = application
        else:
            app = self.defaultApp
        if not app:
            logger.error(f"Application not specified and default application not found.")
            return False
        try:
            process = subprocess.Popen([app, filePath])
            self.processes[filePath] = process
            logger.info(f"Opened file: {filePath} using {app}")
            return True
        except Exception as e:
            logger.error(f"Failed to open file: {filePath}, Error: {e}")
            return False

    def closeFile(self, filePath: str) -> bool:
        """
        Close the file if the application supports it.
        NOTE: This method is not guaranteed to work for all applications. 
        E.g. it does not work for xdg-open on Linux.
        TODO: fix this issue.
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
            logger.error("Entry does not have associated file")
            return False
        
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