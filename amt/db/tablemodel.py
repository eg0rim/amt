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

import  os, tempfile, shutil

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

class DataCache(QObject):
    """Cache to store data changes"""
    cacheDiverged = Signal(bool)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data : list[EntryData] = []
        self._dataToDelete : list[EntryData] = []
        self._dataToEdit : list[EntryData] = []
        self._dataToAdd : list[EntryData] = []
        self._diverged: bool = False
        
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
    def data(self) -> list[EntryData]:
        return self._data
    @data.setter
    def data(self, value: list[EntryData]):
        self._data = value
        self._dataToDelete = []
        self._dataToEdit = []
        self._dataToAdd = [] 
        self.diverged = False   
    
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
        self._data.append(entry)
        self._dataToAdd.append(entry)
        self.diverged = True      
        return True
    
    def remove(self, entry : EntryData) -> bool:
        # first try to remove from add cache
        try: 
            self._dataToAdd.remove(entry)
            self._data.remove(entry)
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
            # add to delete cache
            self._dataToDelete.append(entry)
            # data now differs from the db
            self.diverged = True
            return True
        except ValueError:
            # entry was not in the cache
            return False
            
    def removeByIndex(self, index : int) -> bool:
        if index < 0 or index >= len(self._data):
            return False
        entry = self._data[index]
        return self.remove(entry)
        
    # editing means replacing the entry with a new one
    def edit(self, oldEntry : EntryData, newEntry : EntryData) -> bool:
        # first check if the entry is in the add cache
        try:
            # if the entry is in the add cache, just replace it
            self._dataToAdd[self._dataToAdd.index(oldEntry)] = newEntry
            self._data[self._data.index(oldEntry)] = newEntry
            # entry in add cache does not have an id
            self.diverged = True
            return True
        except ValueError:
            pass
        # if the entry is not in the add cache, try to replace it in the main cache
        try:
            self._data[self._data.index(oldEntry)] = newEntry
            # entry in the main cache has and not in add cache has an id
            newEntry.id = oldEntry.id
            self._dataToEdit.append(newEntry)
            self.diverged = True
            return True
        except ValueError:
            return False
            
    def editByIndex(self, index : int, newEntry : EntryData) -> bool:
        if index < 0 or index >= len(self._data):
            return False
        return self.edit(self._data[index], newEntry)
        
class AMTModel(QAbstractTableModel):
    """Model to manage the articles, books, etc"""
    # signal to notify about changes in the model
    temporaryStatusChanged = Signal(bool)
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
    
    def __init__(self, dbFile : str = None, *args : object):
        """Provides model to interact with db"""
        super().__init__(*args)          
        # cache of data; any non-saved changes to the data are stored here
        self.dataCache : DataCache = DataCache(self)      
        # keep track whether the database is temporary; on change must emit signal
        self._temporary: bool = False
        # if no db file is provided, create a temp file
        if dbFile is None:
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
        
    # implement abstract methods           
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
        return len(self.dataCache.data)
    
    def data(self, index : QModelIndex, role : int = Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return self.entryToDisplayData(self.dataCache.data[index.row()], index.column())
        return None
                                      
    def headerData(self, section : int, orientation : Qt.Orientation, role : int = Qt.DisplayRole) -> object:
        if orientation == Qt.Horizontal and  role == Qt.DisplayRole:
            return self._columnNames[section]
        return None
         
    def sort(self, column : int, order : Qt.SortOrder = Qt.AscendingOrder):
        logger.debug(f"sorting by column {column} order")
        self.beginResetModel()
        self.dataCache.data.sort(key=lambda x: self.entryToDisplayData(x, column))
        if order == Qt.DescendingOrder:
            self.dataCache.data.reverse()
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
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled 
    
    # custom methods
    # prepare tabels 
    def prepareTables(self) -> bool:
        state = True
        for cls in self._supportedDataTypes.values():
            if not cls.createTable(self.db):
                state = False
        return state
        
    # display data
    @classmethod
    def entryToDisplayData(cls, entry : EntryData, column : int) -> str:
        return entry.getDisplayData(cls._columnToField[column])
    
    # manioulate data
    # all changes are stored in cache
    def removeEntriesAt(self, rows : list[int]) -> bool:
        """
        removes entry at given row

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
        """
        logger.info(f"update started")
        self.beginResetModel()
        logger.info(f"extract all entries from db")
        self.dataCache.data = self.extractEntries()
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
        for entry in self.dataCache.dataToAdd[:]:
            #logger.debug(f"insert entry {entry}")
            if not entry.insert(self.db):
                logger.error(f"failed to insert entry {entry}")
                status = False
            self.dataCache.dataToAdd.remove(entry)
        return status
    
    def _submitDelete(self) -> bool:
        """
        submits all deleted entries to the database

        Returns:
            bool: True if successful
        """
        status = True
        for entry in self.dataCache.dataToDelete[:]:
            if not entry.delete(self.db):
                logger.error(f"failed to delete entry {entry}")
                status = False
            self.dataCache.dataToDelete.remove(entry)
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
        logger.debug(f"save changes in cache")
        status =  self._submitAdd() and self._submitDelete() and self._submitEdit()   
        self.dataCache.diverged = False
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
        self.update()
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
            try:
                os.replace(self.db.databaseName(), filePath)
            except OSError as e:
                if e.errno == 18:  # Invalid cross-device link
                    shutil.copy2(self.db.databaseName(), filePath)
                else:
                    raise
            self.db = AMTDatabase(filePath)
            self.db.open()
            logger.debug(f"save db as {filePath}")
            self.temporary = False
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
        return True
        
