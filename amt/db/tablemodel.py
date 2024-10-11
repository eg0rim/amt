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

from PySide6.QtSql import QSqlRecord
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
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

class AMTModel(QAbstractTableModel):
    def __init__(self, dbfile : str, *args : object):
        """Provides model to interact with db"""
        super().__init__(*args)
        self.db = AMTDatabase(dbfile)
        self.db.open()       
        self._columnCount= 3
        self._columnNames = ["Title", "Author(s)", "ArXiv ID"]
        self._columnToField = {0: "title", 1: "authors", 2: "arxivid"}
        self._dataCache : list[EntryData] = []
        self._dataDeleteCache : list[EntryData] = []
        self._dataEditCache : list[EntryData] = []
        self._dataAddCache : list[EntryData] = []
        self._supportedDataTypes: dict[str,EntryData] = {
            "articles": ArticleData,
            "books": BookData,
            "lectures": LecturesData,
            "authors": AuthorData
        }
        self._entryTypes = ["articles", "books", "lectures"]
        for cls in self._supportedDataTypes.values():
            cls.createTable(AMTQuery(self.db))
        self._changed = False
        
    def entryToDisplayData(self, entry : EntryData, column : int) -> str:
        return entry.getDisplayData(self._columnToField[column])
        
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
        return len(self._dataCache)
    
    def data(self, index : QModelIndex, role : int = Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return self.entryToDisplayData(self._dataCache[index.row()], index.column())
        return None
                                      
    def headerData(self, section : int, orientation : Qt.Orientation, role : int = Qt.DisplayRole) -> object:
        if orientation == Qt.Horizontal and  role == Qt.DisplayRole:
            return self._columnNames[section]
        return None
         
    def sort(self, column : int, order : Qt.SortOrder = Qt.AscendingOrder):
        logger.debug(f"sorting by column {column} order")
        self.beginResetModel()
        self._dataCache.sort(key=lambda x: self.entryToDisplayData(x, column))
        if order == Qt.DescendingOrder:
            self._dataCache.reverse()
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
            entry = self._dataCache.pop(row)
            self._dataDeleteCache.append(entry)
            logger.info(f"remove entry {entry}")
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
        if row < 0 or row >= len(self._dataCache):
            return False
        self.beginResetModel()
        self._dataCache[row] = newEntry
        self._dataEditCache.append(newEntry)
        logger.info(f"edit entry {newEntry}")
        self.endResetModel()
        return True
    
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
        
    def update(self) -> bool:
        logger.info(f"update started")
        self.beginResetModel()
        logger.info(f"remove all rows")
        self._dataCache = []
        logger.info(f"extract all entries from db")
        data = self.extractEntries()
        logger.info(f"insert all rows")
        self._dataCache = data
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
        logger.info(f"add entry {entry}")
        self.beginInsertRows(QModelIndex(), len(self._dataCache), len(self._dataCache))
        self._dataCache.append(entry)
        self._dataAddCache.append(entry)
        self.endInsertRows()
        return True
    
    def submitAdd(self) -> bool:
        """
        submits all added entries to the database

        Returns:
            bool: True if successful
        """
        status = True
        query = AMTQuery(self.db)
        for entry in self._dataAddCache:
            if entry.insert(query):
                self._dataAddCache.remove(entry)
            else:
                logger.error(f"failed to insert entry {entry}; it is still in add cache")
                status = False
        return status
    
    def submitDelete(self) -> bool:
        """
        submits all deleted entries to the database

        Returns:
            bool: True if successful
        """
        status = True
        query = AMTQuery(self.db)
        for entry in self._dataDeleteCache:
            if entry.delete(query):
                self._dataDeleteCache.remove(entry)
            else:
                logger.error(f"failed to delete entry {entry}; it is still in delete cache")
                status = False
        return status
    
    def submitEdit(self) -> bool:
        """
        submits all edited entries to the database

        Returns:
            bool: True if successful
        """
        status = True
        query = AMTQuery(self.db)
        for entry in self._dataEditCache:
            if entry.update(query):
                self._dataEditCache.remove(entry)
            else:
                logger.error(f"failed to update entry {entry}; it is still in edit cache")
                status = False
        return status
    
    def submitAll(self) -> bool:
        """
        submits all changes to the database

        Returns:
            bool: True if successful
        """
        return self.submitAdd() and self.submitDelete() and self.submitEdit()   

