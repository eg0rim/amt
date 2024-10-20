# -*- coding: utf-8 -*-
# amt/db/model.py

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

"""model to manage the articles, books, etc"""

import  tempfile, shutil, re

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal, QObject
from .database import AMTDatabase, AMTQuery
from .datamodel import (
    AuthorData,
    ArticleData,
    BookData,
    LecturesData,
    EntryData
)

from amt.logger import getLogger

logger = getLogger(__name__) 

class AMTFilter:
    """ 
    Filter object contains information about the filter: pattern, fields to search in, if search is case independent and if pattern should be escaped.
    Properties:
        pattern (str): pattern to search for
        fields (list[str]): fields to search in
        escape (bool): if True, pattern is escaped
    Methods:
        __init__(self, field: str | list[str] = [], pattern: str = "", escape: bool = True, caseIndependent: bool = True)
        addField(self, field: str)
        removeField(self, field: str)
        test(self, entry: EntryData) -> bool
        apply(self, data: list[EntryData]) -> list[EntryData]
    """
    def __init__(self, field : str | list[str] = [], pattern : str = "", escape : bool = True, caseIndependent : bool = True):
        """ 
        Constructor for the filter object.
        Args:
            field (str | list[str]): field or list of fields to search in
            pattern (str): pattern to search for
            escape (bool): if True, pattern is escaped
            caseIndependent (bool): if True, search is case independent
        """
        super().__init__()
        self._pattern: str = pattern
        self._fields: list[str] = []
        self._fields.append(field) if isinstance(field, str) else self._fields.extend(field)
        self._escape: bool = escape
        self._caseIndependent: bool = caseIndependent
        
    def addField(self, field : str):
        """ 
        Adds a field to the filter.
        """
        self._fields.append(field)
        
    def removeField(self, field : str):
        """ 
        Removes a field from the filter.
        """
        try:
            self._fields.remove(field)
        except ValueError:
            logger.error(f"field {field} not found")
        
    @property
    def pattern(self) -> str:
        return self._pattern
    @pattern.setter
    def pattern(self, value: str):
        self._pattern = value
        
    @property   
    def fields(self) -> list[str]:
        return self._fields
    @fields.setter
    def fields(self, value: list[str]):
        self._fields = value
        
    @property
    def escape(self) -> bool:
        return self._escape
    @escape.setter
    def escape(self, value: bool):
        self._escape = value
        
    def test(self, entry : EntryData) -> bool:
        """ 
        Apply the filter to the entry.
        Args:
            entry (EntryData): entry to test
        Returns:
            bool: True if the entry passes the filter
        """
        if self.pattern and self.fields:
            pattern = self.pattern.lower() if self._caseIndependent else self.pattern
            if self.escape:
                regex = re.compile(re.escape(pattern))
            else: 
                # catch error if pattern is not a valid regex
                try:
                    regex = re.compile(pattern)
                except re.error:
                    # let everything pass if pattern is not valid
                    return True
                regex = re.compile(pattern)
            if self._caseIndependent:
                return any([regex.search(entry.getDisplayData(field).lower()) for field in self.fields])
            else:
                return any([regex.search(entry.getDisplayData(field)) for field in self.fields])
        return True
        
    def apply(self, data : list[EntryData]) -> list[EntryData]:
        """ 
        Apply the filter to the list of entries.
        Args:
            data (list[EntryData]): list of entries
        Returns:
            list[EntryData]: list of entries that pass the filter
        """
        if self.pattern and self.fields:
            filtered =  [entry for entry in data if self.test(entry)]
            return filtered
        else:
            return data[:]

class DataCache(QObject):
    """
    Class QObject to store the data and changes to the data.
    Signals:
        dataReset: emitted when the data is reset
        cacheDiverged: emitted when the cache differs from the initial set data
    Properties:
        diverged (bool): True if the cache differs from initial set data
        filter (AMTFilter): filter to apply to the data
        dataToDisplay (list[EntryData]): data to display
        data (list[EntryData]): all data
        dataToDelete (list[EntryData]): data to delete
        dataToEdit (list[EntryData]): data to edit
        dataToAdd (list[EntryData]): data to add
    Methods:
        add(self, entry: EntryData) -> bool
        remove(self, entry: EntryData) -> bool
        removeByIndex(self, index: int) -> bool
        edit(self, oldEntry: EntryData, newEntry: EntryData) -> bool
        editByIndex(self, index: int, newEntry: EntryData) -> bool
        resetChangeCache(self) -> None
        updateDataToDisplay(self) -> None
    """
    dataReset = Signal()
    cacheDiverged = Signal(bool)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data : list[EntryData] = []
        self._dataToDelete : list[EntryData] = []
        self._dataToEdit : list[EntryData] = []
        self._dataToAdd : list[EntryData] = []
        self._dataToDisplay : list[EntryData] = []
        self._diverged: bool = False
        self._filter: AMTFilter = None
        self.dataReset.connect(self.resetChangeCache)
        self.filter = AMTFilter()
        
    @property
    def diverged(self) -> bool:
        return self._diverged
    @diverged.setter
    def diverged(self, value: bool):
        if value == self._diverged:
            return
        self._diverged = value
        self.cacheDiverged.emit(value)
        
    @property
    def filter(self) -> AMTFilter:
        return self._filter
    @filter.setter
    def filter(self, value: AMTFilter):
        self._filter = value
        self._dataToDisplay = self._filter.apply(self._data)
        logger.debug(f"filter set to {value.pattern} {value.fields} {value.escape} ")
        
    @property
    def dataToDisplay(self) -> list[EntryData]:
        return self._dataToDisplay
        
    @property
    def data(self) -> list[EntryData]:
        return self._data
    @data.setter
    def data(self, value: list[EntryData]):
        self._data = value
        self.updateDataToDisplay()
        self.dataReset.emit()
    
    @property
    def dataToDelete(self) -> list[EntryData]:
        return self._dataToDelete
    
    @property
    def dataToEdit(self) -> list[EntryData]:
        return self._dataToEdit
    
    @property
    def dataToAdd(self) -> list[EntryData]:
        return self._dataToAdd
      
    def add(self, entry : EntryData) -> bool:
        """
        adds entry to the cache
        Args:
            entry (EntryData): entry to add
        Returns:
            bool: True if the entry was added
        """
        self.data.append(entry)
        self.dataToAdd.append(entry)
        self.updateDataToDisplay()
        self.diverged = True      
        return True
    
    def remove(self, entry : EntryData) -> bool:
        """ 
        Removes entry from the cache.
        Args:
            entry (EntryData): entry to remove
        Returns:
            bool: True if the entry was removed
        """
        # first try to remove from add cache
        try: 
            self._dataToAdd.remove(entry)
            self._data.remove(entry)
            self.updateDataToDisplay()
            # if the entry is in add cache, it is not in the db
            # check if anything in the editing cache
            if not (self._dataToAdd or self._dataToEdit or self._dataToDelete):
                # if all caches are empty, cache is not diverged anymore
                self.diverged = False
            return True
        except ValueError:
            pass
        # if not in add cache, try to remove from the edit cache
        try:    
            self._dataToEdit.remove(entry)
            self._data.remove(entry)
            self.updateDataToDisplay()
            # if the entry is in edit cache, it is not in the db
            # check if anything in the editing cache
            if not (self._dataToAdd or self._dataToEdit or self._dataToDelete):
                # if all caches are empty, cache is not diverged anymore
                self.diverged = False
            return True
        except ValueError:
            pass
        # if not in edit cache, try to remove from the main cache
        try:
            self._data.remove(entry)
            self.updateDataToDisplay()
            # add to delete cache
            self._dataToDelete.append(entry)
            # data now differs from the db
            self.diverged = True
            return True
        except ValueError:
            # entry was not in the cache
            return False
            
    def removeByIndex(self, index : int) -> bool:
        """ 
        Removes entry at given index.
        Args:
            index (int): index of the entry
        Returns:
            bool: True if the entry was removed
        """
        if index < 0 or index >= len(self._data):
            return False
        entry = self._dataToDisplay[index]
        return self.remove(entry)
        
    # editing means replacing the entry with a new one
    def edit(self, oldEntry : EntryData, newEntry : EntryData) -> bool:
        """ 
        Edits entry in the cache.
        Args:
            oldEntry (EntryData): entry to replace
            newEntry (EntryData): new entry
        Returns:
            bool: True if the entry was edited
        """
        # first check if the entry is in the add cache
        try:
            # if the entry is in the add cache, just replace it
            self._dataToAdd[self._dataToAdd.index(oldEntry)] = newEntry
            self._data[self._data.index(oldEntry)] = newEntry
            self.updateDataToDisplay()
            # entry in add cache does not have an id
            self.diverged = True
            return True
        except ValueError:
            pass
        # if the entry is not in the add cache, try to replace it in the main cache
        try:
            self._data[self._data.index(oldEntry)] = newEntry
            self.updateDataToDisplay()
            # entry in the main cache has and not in add cache has an id
            newEntry.id = oldEntry.id
            self._dataToEdit.append(newEntry)
            self.diverged = True
            return True
        except ValueError:
            return False
            
    def editByIndex(self, index : int, newEntry : EntryData) -> bool:
        """ 
        Edits entry at given index.
        Args:
            index (int): index of the entry
            newEntry (EntryData): new entry
        Returns:
            bool: True if the entry was edited
        """
        if index < 0 or index >= len(self._data):
            return False
        return self.edit(self._dataToDisplay[index], newEntry)
    
    def sort(self, field : str, order : Qt.SortOrder = Qt.AscendingOrder):
        """ 
        Sorting of the data base on a field of the entries.
        Args:
            column (int): column number
            order (Qt.SortOrder, optional): sorting order. Defaults to Qt.AscendingOrder
        """
        self._data.sort(key=lambda x: x.getDisplayData(field))
        if order == Qt.DescendingOrder:
            self._data.reverse()
        self.updateDataToDisplay()
    
    def resetChangeCache(self):
        """ 
        Reset data in change cache.
        """
        self._dataToDelete = []
        self._dataToEdit = []
        self._dataToAdd = []
        self.diverged = False
                
    def updateDataToDisplay(self):
        """ 
        Update the data to display.
        """
        self._dataToDisplay = self._filter.apply(self._data)
    
class AMTModel(QAbstractTableModel):
    """
    Model to manage the articles, books, etc.
    Inherits from QAbstractTableModel.
    Signals:
        temporaryStatusChanged (bool): emitted when the temporary status of the model changes. Emits True if the model is temporary
        databaseConnected (str): emitted when the database is connected. Emits the path to the database
    Class attributes:
        _columnNames (list[str]): list of column names
        _columnCount (int): number of columns
        _columnToField (dict[int, str]): mapping of columns to fields in the data model
        _supportedDataTypes (dict[str, EntryData]): supported data types
        _entryTypes (list[str]): data types that are shown in the corresponding table view
    Properties:
        temporary (bool): True if the model is temporary
    Attributes:
        dataCache (DataCache): cache of data
        db (AMTDatabase): database
    Methods:
        __init__(self, dbFile: str = "", *args: object) -> None
        columnCount(self, parent: QModelIndex = None) -> int
        rowCount(self, parent: QModelIndex = None) -> int
        data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any
        headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any
        sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None
        flags(self, index: QModelIndex) -> Qt.ItemFlags
        prepareTables(self) -> bool
        updateTableColumns(self) -> bool
        entryToDisplayData(cls, entry: EntryData, column: int) -> str
        removeEntriesAt(self, rows: list[int]) -> bool
        editEntryAt(self, row: int, newEntry: EntryData) -> bool
        addEntry(self, entry: EntryData) -> bool
        extractEntries(self) -> list[EntryData]
        update(self) -> bool
        filter(self, filter: AMTFilter) -> bool
        saveDB(self) -> bool
        openExistingDB(self, filePath: str) -> bool
        saveDBAs(self, filePath: str) -> bool
        createNewTempDB(self) -> bool
        getDataAt(self, index: int) -> EntryData
    """
    # signal to notify about changes in the model
    temporaryStatusChanged = Signal(bool)
    databaseConnected = Signal(str)
    # specify columns
    _columnNames: list[str] = ["Title", "Author(s)", "ArXiv ID"]
    _columnCount: int = len(_columnNames)
    # map columns to fields in datamodel
    _columnToField: dict[int, str] = {0: "title", 1: "authors", 2: "arxivid"}
    # supported data types; if new data types are added, they should be added here
    _supportedDataTypes: dict[str,EntryData] = {
        "articles": ArticleData,
        "books": BookData,
        "lectures": LecturesData,
        "authors": AuthorData
    }
    # data types that are shown in the corresponding table view
    _entryTypes = ["articles", "books", "lectures"]
    
    def __init__(self, dbFile : str = "", *args : object):
        """
        Constructor for the model.
        Args:
            dbFile (str): path to the database file. If not provided, a temporary database is created
            *args (object): arguments for the parent class
        """
        super().__init__(*args)          
        # cache of data; any non-saved changes to the data are stored here
        self.dataCache : DataCache = DataCache(self)      
        # keep track whether the database is temporary; on change must emit signal
        self._temporary: bool = False
        # if no db file is provided, create a temp file
        self.db : AMTDatabase = None
        # create empty db if dbfile is not provided
        if not dbFile:
            self.createNewTempDB()
        else:
            self.openExistingDB(dbFile)       
            
    @property
    def temporary(self) -> bool:
        return self._temporary
    @temporary.setter
    def temporary(self, value: bool):
        if value == self._temporary:
            return
        self._temporary = value
        self.temporaryStatusChanged.emit(value)
        
    # implement abstract methods from QAbstractTableModel     
    def columnCount(self, parent : QModelIndex = None) -> int:
        """
        total number of columns in the model
        it is a fixed number corresponding to the number of columns in gui

        Args:
            parent (QModelIndex, optional): parent index. Defaults to None.

        Returns:
            int: number of columns
        """
        return self._columnCount
    
    def rowCount(self, parent : QModelIndex = None) -> int:
        """
        total number of rows

        Args:
            parent (QModelIndex, optional): parent index. Defaults to None.

        Returns:
            int: number of rows
        """
        return len(self.dataCache.dataToDisplay)
    
    def data(self, index : QModelIndex, role : int = Qt.DisplayRole):
        """ 
        data for the given index
        
        Args:
            index (QModelIndex): index
            role (int, optional): role. Defaults to Qt.DisplayRole.
        """
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return self.entryToDisplayData(self.dataCache.dataToDisplay[index.row()], index.column())
        return None
                                      
    
    def headerData(self, section : int, orientation : Qt.Orientation, role : int = Qt.DisplayRole) -> object:
        """ 
        returns the header data for the given section
        Args:
            section (int): section number
            orientation (Qt.Orientation): orientation (Horizonatal of Vertical)
            role (int, optional): role. Defaults to Qt.DisplayRole.
        Returns:
            object: header data
        """
        if orientation == Qt.Horizontal and  role == Qt.DisplayRole:
            return self._columnNames[section]
        return None
         
    def sort(self, column : int, order : Qt.SortOrder = Qt.AscendingOrder):
        """
        Sorting of the data.
        Args:
            column (int): column number
            order (Qt.SortOrder, optional): sorting order. Defaults to Qt.AscendingOrder
        """
        logger.debug(f"sorting by column {column} order {order}")
        self.beginResetModel()
        self.dataCache.sort(self._columnToField[column], order)
        self.endResetModel()
    
    # the code is not needed as we do not allow editing from QTableView        
    # def removeRows(self, row : int, count : int, parent : QModelIndex = QModelIndex()) -> bool:
    #     self.beginRemoveRows(QModelIndex(), row, row + count - 1)
    #     self._dataCache = self._dataCache[:row] + self._dataCache[row + count:]
    #     logger.debug("TODO: add removing from db")
    #     self.endRemoveRows()
    #     return True
    
    # def setData(self, index : QModelIndex, value : object, role : int = Qt.EditRole) -> bool:
    #     logger.debug(f"set data {value} at {index.row()} {index.column()}")
    #     if not index.isValid() or role != Qt.EditRole:
    #         return False
    #     #if index.column() == 0:
    #     #    #self._dataCache[index.row()].title = value
    #     #elif index.column() == 1:
    #     #    #self._dataCache[index.row()].authors = value
    #     #else:
    #     #    return False
    #     self.dataChanged.emit(index, index)
    #     return True
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """ 
        Flags for the given index.
        Args:
            index (QModelIndex): index
        Returns:
            Qt.ItemFlags: flags
        """
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled 
    
    # custom methods
    # prepare tabels 
    def prepareTables(self) -> bool:
        """ 
        Prepare tables in the database for all supported data types.
        Create table or update them with new columns if needed.
        Returns:
            bool: True if successful
        """
        state = True
        for cls in self._supportedDataTypes.values():
            if not cls.createTable(self.db):
                state = False
        return state
    
    # update table columns
    def updateTableColumns(self) -> bool:
        """ 
        Update table columns for all supported data types.
        Returns:
            bool: True if successful
        """
        state = True
        for cls in self._supportedDataTypes.values():
            if not cls.extendTableColumns(self.db):
                state = False
        return state
        
    # display data
    @classmethod
    def entryToDisplayData(cls, entry : EntryData, column : int) -> str:
        """ 
        Transforms the entry data to the string representation for the given column.
        Args:
            entry (EntryData): entry
            column (int): column number
        Returns:
            str: string representation of the entry data
        """
        return entry.getDisplayData(cls._columnToField[column])
    
    # manioulate data
    # all changes are stored in cache
    def getDataAt(self, index : int) -> EntryData:
        """
        returns the entry at given index

        Args:
            index (int): index

        Returns:
            EntryData: entry
        """
        return self.dataCache.dataToDisplay[index]
    
    def removeEntriesAt(self, rows : list[int]) -> bool:
        """
        removes entry at given rows

        Args:
            row (int): row number

        Returns:
            bool: True if successful
        """
        self.beginResetModel()
        for row in rows:
            self.dataCache.removeByIndex(row)
        self.endResetModel()
        return True
    
    
    def editEntryAt(self, row : int, newEntry : EntryData) -> bool:
        """
        edits entry at given row

        Args:
            row (int): row number
            newEntry (EntryData): new entry

        Returns:
            bool: True if successful
        """
        self.beginResetModel()
        self.dataCache.editByIndex(row, newEntry)
        self.endResetModel()
        return True
    
    def addEntry(self, entry : EntryData) -> bool:
        """
        adds entry to the model

        Args:
            entry (EntryData): entry to add

        Returns:
            bool: True if successful
        """
        self.beginInsertRows(QModelIndex(), len(self.dataCache.data), len(self.dataCache.data))
        self.dataCache.add(entry)
        self.endInsertRows()
        return True
    
    # extract entries from the database
    def extractEntries(self) -> list[EntryData]:
        """
        extracts all entries from article, book and lecture tables

        Returns:
            tuple of lists containing EntryData objects and lists of its str representation
        """
        data = []
        query = AMTQuery(self.db)
        for table in self._entryTypes:
            cls = self._supportedDataTypes[table]
            data += cls.extractData(query)
        return data
        
    # update the model with the data from the database
    def update(self) -> bool:
        """ 
        updates the model with the data from the database
        Returns:
            bool: True if successful
        """
        logger.info(f"update started")
        self.beginResetModel()
        logger.info(f"extract all entries from db")
        self.dataCache.data = self.extractEntries()
        self.endResetModel()
        return True
    
    def filter(self, filter : AMTFilter) -> bool:
        """ 
        Filters the data. 
        Args:
            filter (AMTFilter): filter object 
        Returns:    
            bool: True if successful
        """
        self.beginResetModel()
        self.dataCache.filter = filter
        self.endResetModel()
        return True
    
    #submit changes to the database
    def _submitAdd(self) -> bool:
        """
        submits all added entries to the database

        Returns:
            bool: True if successful
        """
        status = True
        if len(self.dataCache.dataToAdd) == 0:
            return status
        elif len(self.dataCache.dataToAdd) < 10: 
            for entry in self.dataCache.dataToAdd[:]:
                #logger.debug(f"insert entry {entry}")
                if not entry.insert(self.db):
                    logger.error(f"failed to insert entry {entry}")
                    status = False
                self.dataCache.dataToAdd.remove(entry)
        else:
            for entryType in self._entryTypes:
                entryCls = self._supportedDataTypes[entryType]
                dataToInsert = [entry for entry in self.dataCache.dataToAdd if isinstance(entry, entryCls)]
                if len(dataToInsert) == 0:
                    continue
                if not entryCls.insertMultiple(self.db, dataToInsert):
                    logger.error(f"failed to insert multiple entries {dataToInsert}")
                    status = False        
            self.dataCache.dataToAdd.clear()
        return status
    
    def _submitDelete(self) -> bool:
        """
        submits all deleted entries to the database

        Returns:
            bool: True if successful
        """
        status = True
        if len(self.dataCache.dataToDelete) == 0:
            return status
        elif len(self.dataCache.dataToDelete) < 10: 
            for entry in self.dataCache.dataToDelete[:]:
                if not entry.delete(self.db):
                    logger.error(f"failed to delete entry {entry}")
                    status = False
                self.dataCache.dataToDelete.remove(entry)
        else:
            for entryType in self._entryTypes:
                entryCls = self._supportedDataTypes[entryType]
                dataToDelete = [entry for entry in self.dataCache.dataToDelete if isinstance(entry, entryCls)]
                if len(dataToDelete) == 0:
                    continue
                if not entryCls.deleteMultiple(self.db, dataToDelete):
                    logger.error(f"failed to delete multiple entries {dataToDelete}")
                    status = False        
            self.dataCache.dataToDelete.clear()
        return status
    
    def _submitEdit(self) -> bool:
        """
        submits all edited entries to the database

        Returns:
            bool: True if successful
        """
        status = True
        for entry in self.dataCache.dataToEdit[:]:
            if not entry.update(self.db):
                logger.error(f"failed to update entry {entry}")
                status = False
            self.dataCache.dataToEdit.remove(entry)
        return status
    
    # database file operations    
    def saveDB(self) -> bool:
        """
        saves all changes to the database

        Returns:
            bool: True if successful
        """
        try: 
            logger.debug(f"save changes in cache")
            status =  self._submitAdd() and self._submitDelete() and self._submitEdit()   
            self.dataCache.diverged = False
        except Exception as e:
            logger.error(f"failed to save changes: {e}")
            status = False
        return status
    
    def openExistingDB(self, filePath : str) -> bool:
        """
        opens the database

        Args:
            filePath (str): file path

        Returns:
            bool: True if successful
        """
        self.db = AMTDatabase(filePath)
        #self.prepareTables()
        self.db.open()
        self.temporary = False
        self.updateTableColumns()
        self.update()
        self.databaseConnected.emit(filePath)
        logger.info(f"database opened: {filePath}")
        return True    
    
    def saveDBAs(self, filePath : str) -> bool:
        """
        saves the database to a file

        Args:
            filePath (str): file path

        Returns:
            bool: True if successful
        """
        # copy the current file to the new location
        try:
            self.db.close()
            shutil.copy2(self.db.databaseName(), filePath)
            self.db = AMTDatabase(filePath)
            self.db.open()
            logger.debug(f"save db as {filePath}")
            self.temporary = False
            self.databaseConnected.emit(filePath)
            logger.info(f"database saved as {filePath}")
            return self.saveDB()
        except Exception as e:
            logger.error(f"failed to save database as {filePath}: {e}")
            return False
        
    def createNewTempDB(self) -> bool:
        """
        creates a new temporary database

        Returns:
            bool: True if successful
        """
        tmpFile = tempfile.NamedTemporaryFile(delete=False, suffix=".amtdb")
        logger.info(f"using temp file {tmpFile.name}")
        self.db = AMTDatabase(tmpFile.name)
        tmpFile.close()
        self.db.open()
        logger.debug(f"create new db {tmpFile.name}")
        self.temporary = True
        self.prepareTables()
        self.update()
        self.databaseConnected.emit("")
        return True
        
