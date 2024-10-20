# -*- coding: utf-8 -*-
# amt/db/datamodel.py

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

"""objects to store various data"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar
from PySide6.QtCore import (
    QDate,
    QDateTime,
    Qt
)
import subprocess
from amt.db.database import AMTDatabase, AMTQuery
from amt.logger import getLogger

logger = getLogger(__name__)

T = TypeVar('T', bound='AbstractData')

class AbstractData(ABC):
    """
    Abstract class for data storage and its insertion, deletion, update, etc. to specified database.
    Class attributes: 
        tableName: str - table name corresponding to the data type. Must be specified in subclasses
        tableColumns: dict[str, str] - table columns must be specified in the order of their appearance in the table with type and constraints.
        tableAddLines: list[str] - additional lines needed for create query. 
    Properties:
        id: int - id of the data. Must be specified only to existing data in database. For new data it is must be None. Insertion must assign id.
    Methods:
        createEmptyInstance() -> 'AbstractData'
        createTable(db: AMTDatabase) -> bool
        extendTableColumns(db: AMTDatabase) -> bool
        select(db: AMTDatabase, filter: str = "") -> bool
        getDataToInsert() -> dict[str, str]
        insert(db: AMTDatabase) -> bool
        delete(db: AMTDatabase) -> bool
        update(db: AMTDatabase) -> bool
        fillFromRow(row: list[str]) -> list[str]
        fromRow(row: list[str]) -> 'AbstractData'
        extractData(db: AMTDatabase, filter: str = "") -> list['AbstractData']
        toString() -> str
        toShortString() -> str
        getDisplayData(field: str) -> str
    """
    # table name corresponding to the data type
    tableName: str = None
    # table columns must be specified in the order of their appearance in the table
    # with type and constraints
    # for example: {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "name": "TEXT NOT NULL"}
    tableColumns: dict[str, str] = {"id": "INTEGER PRIMARY KEY AUTOINCREMENT"}
    # additional lines needed for create query
    # for example: ["UNIQUE(name)"]
    tableAddLines: list[str] = []
    def __init__(self):
        super().__init__()
        # id must be specified only to existing data in database
        # for new data it is must be None
        # insertion must assign id
        self._id: int = None
    
    @property
    def id(self) -> int:
        return self._id
    
    @id.setter
    def id(self, value : int):
        self._id = value
        
    @classmethod    
    @abstractmethod
    def createEmptyInstance(cls: Type[T]) -> T:
        """
        Create empty instance of the data object.
        Must be implemented in subclasses.
        """
        pass
           
    @classmethod
    def createTable(cls, db : AMTDatabase) -> bool:
        """ 
        Create table in the database corresponding to the data type.
        Args:
            db (AMTDatabase): database object
        Returns:
            bool: True if table created successfully, False otherwise
        """
        query = AMTQuery(db)
        if not query.createTable(cls.tableName, cls.tableColumns, ifNotExists=True): #, addLines=cls.tableAddLines):
            return False
        return query.exec()
    
    @classmethod
    def extendTableColumns(cls, db : AMTDatabase) -> bool:
        """ 
        Extend existing table corresponding to the data type in the database with the new columns.
        Args:
            db (AMTDatabase): database object
        Returns:
            bool: True if table columns updated successfully, False otherwise
        """
        state = True
        query = AMTQuery(db)
        currentColumns = query.getTableInfo(cls.tableName)
        newColumns = cls.tableColumns
        newColumnsToAdd = {k: v for k, v in newColumns.items() if k not in currentColumns.keys()}
        if not newColumnsToAdd:
            return True
        logger.warning(f"The database has missing columns in the table {cls.tableName}: {newColumnsToAdd}")
        logger.warning(f"Trying to add missing columns")
        for col, colType in newColumnsToAdd.items():
            if not query.alterTable(cls.tableName, "ADD", col, colType):
                state = False
            if not query.exec():
                state = False
        if state:
            logger.warning(f"Added missing columns to the table {cls.tableName}")
        return state
        # if not query.updateTableColumns(cls.tableName, cls.tableColumns):
        #     return False
        # return query.exec()
    
    @classmethod
    def select(cls, db : AMTDatabase, filter : str = "") -> bool:
        """ 
        Select data from the table corresponding to the data type.
        Args:
            db (AMTDatabase): database object
            filter (str, optional): filter string. Defaults to "".
        Returns:
            bool: True if select query executed successfully, False otherwise
        """
        query = AMTQuery(db)
        if not query.select(cls.tableName, cls.tableColumns.keys(), filter):
            return False
        return query.exec()
    
    def getDataToInsert(self) -> dict[str, str]:
        """
        Get data to insert into the table.
        Baseclass implementation returns only id.
        Returns:
            dict[str, str]: dictionary of column names and values. values can be None, corresponding to NULL in SQL
        """
        data = {}
        if self.id:
            data["id"] = str(self.id)
        return data
    
    @classmethod
    def insertMultiple(cls : Type[T], db : AMTDatabase, data : list[T]) -> bool:
        """ 
        Insert multiple data objects into the table corresponding to the data type.
        WARNING: list of data objects must be of the same type.
        Args:
            db (AMTDatabase): database object
            data (list[AbstractData]): list of data objects
        Returns:
            bool: True if insert query executed successfully, False otherwise
        """
        query = AMTQuery(db)
        dataToInsert = [d.getDataToInsert() for d in data]
        if not query.insert(cls.tableName, dataToInsert):
            return False
        if not query.exec():
            return False
        # get ids of the inserted data
        lastId = query.lastInsertId()
        for i, d in enumerate(data):
            d.id = lastId + i - len(data) + 1
        return True
        
    def insert(self, db : AMTDatabase) -> bool:
        """ 
        Insert data into the table corresponding to the data type.
        Args:
            db (AMTDatabase): database object
        Returns:
            bool: True if insert query executed successfully, False otherwise
        """
        query = AMTQuery(db)
        if not query.insert(self.tableName, self.getDataToInsert()):
            return False
        if not query.exec():
            return False
        # get id of the inserted data
        self.id = query.lastInsertId()
        return True
    
    @classmethod
    def deleteMultiple(cls : Type[T], db : AMTDatabase, data : list[T]) -> bool:
        """ 
        Delete multiple data objects from the table corresponding to the data type.
        WARNING: list of data objects must be of the same type.
        Args:
            db (AMTDatabase): database object
            data (list[AbstractData]): list of data objects
        Returns:
            bool: True if delete query executed successfully, False otherwise
        """
        ids = [str(d.id) for d in data]
        if any(id is None for id in ids):
            logger.error("Cannot delete data without id: {ids}")
            return False
        query = AMTQuery(db)
        if not query.delete(cls.tableName, f"id IN ({','.join(ids)})"):
            return False
        if not query.exec():
            return False
        for d in data:
            d.id = None
        return True
    
    def delete(self, db : AMTDatabase) -> bool:
        """ 
        Delete data from the table corresponding to the data type.
        Args:
            db (AMTDatabase): database object
        Returns:
            bool: True if delete query executed successfully, False otherwise
        """
        if not self.id:
            logger.error("Cannot delete data without id")
            return False
        query = AMTQuery(db)
        if not query.delete(self.tableName, f"id = {self.id}"):
            return False
        if not query.exec():
            return False
        self.id = None
        return True
    
    def update(self, db : AMTDatabase) -> bool:
        """ 
        Update data in the table corresponding to the data type.
        Args:
            db (AMTDatabase): database object
        Returns:    
            bool: True if update query executed successfully, False otherwise
        """
        if not self.id:
            logger.error("Cannot update data without id")
            return False
        query = AMTQuery(db)
        dataToInsert = self.getDataToInsert()
        dataToInsert.pop("id", None)
        if not query.update(self.tableName, dataToInsert, f"id = {self.id}"):
            return False
        if not query.exec():
            return False
        return True     
    
    def fillFromRow(self, row : list[str]) -> list[str]:
        """
        Fill data object from row returned by select query.
        The trailing elements of the row that are not used by the data object are returned.
        Args:
            row (list[str]): row returned by select query
        Returns:
            list[str]: trailing elements of the row that are not used by the data object
        """
        self.id = row[0]
        return row[1:]
    
    @classmethod
    def fromRow(cls, row : list[str]) -> 'AbstractData':
        """
        Create data object from row returned by select query.
        Args:
            row (list[str]): row returned by select query
        Returns:
            AbstractData: data object
        """
        obj = cls.createEmptyInstance()
        rrow = obj.fillFromRow(row)
        if rrow:
            logger.warning(f"{cls.__name__} did not use all row elements: {rrow}")
        return obj
    
    @classmethod 
    def extractData(cls, db : AMTDatabase, filter : str = "") -> list['AbstractData']:
        """ 
        Extract data from the table corresponding to the data type based on the filter.
        Args:
            db (AMTDatabase): database object
            filter (str, optional): filter string. Defaults to "".
        Returns:
            list[AbstractData]: list of data objects
        """
        query = AMTQuery(db)
        query.select(cls.tableName, cls.tableColumns.keys(), filter)
        query.exec()
        if not query.execStatus or not query.getState("select"):
            logger.error("Invalid query state")
            return None    
        data = []
        while query.next():
            row = [query.value(i) for i in range(len(cls.tableColumns))]
            data.append(cls.fromRow(row))
        return data
    
    def toString(self) -> str:
        """ 
        String representation of the data.
        Must only return str.
        """
        return ""
    
    def toShortString(self) -> str:
        """ 
        Short string representation of the data.
        Must only return str.
        """
        return ""
    
    def getDisplayData(self, field : str) -> str:
        """
        Get data to display in the view.
        Must only return str.
        
        Args:
            field (str): field name
            
        Returns:
            str: data to display
        """
        if field == "id":
            return str(self.id) if self.id else ""
        # elif field == "name":
        #     return self.toString() 
        # elif field == "shortName":
        #     return self.toShortString()      
        return ""

class OrganizationData(AbstractData):
    """
    Data type to store organization data like universities, research centers, etc.
    """
    tableName = "organizations"
    tableColumns = AbstractData.tableColumns.copy()
    tableColumns.update({"name": "TEXT NOT NULL", "short_name": "TEXT", "address": "TEXT", "info": "TEXT"})
    def __init__(self, orgName : str):
        super().__init__()
        self._name: str = orgName
        self._shortName: str = None
        self._address: str = None
        self._info: str = None
        
    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value : str):
        self._name = value

    @property
    def shortName(self) -> str:
        return self._shortName

    @shortName.setter
    def shortName(self, value : str):
        self._shortName = value

    @property
    def address(self) -> str:
        return self._address

    @address.setter
    def address(self, value : str):
        self._address = value

    @property
    def info(self) -> str:
        return self._info

    @info.setter
    def info(self, value : str):
        self._info = value
        
    @classmethod    
    def createEmptyInstance(cls) -> 'OrganizationData':
        return OrganizationData("")
    
    def fillFromRow(self, row: list[str]) -> None:
        nrow = super().fillFromRow(row)
        self.name = nrow[0]
        self.shortName = nrow[1]
        self.address = nrow[2]
        self.info = nrow[3] 
        return nrow[4:]
        
    def getDataToInsert(self) -> dict[str, str]:
        data = super().getDataToInsert()
        data["name"] = self.name
        data["short_name"] = self.shortName
        data["address"] = self.address
        data["info"] = self.info
        return data
        
    def toString(self):
        return self.name or ""
    
    def toShortString(self):
        return self.shortName or ""
    
    def getDisplayData(self, field: str) -> str:
        if field == "address":
            return self.address or ""
        elif field == "info":
            return self.info
        elif field == "name":
            return self.name
        elif field == "shortName":
            return self.shortName
        return super().getDisplayData(field)
    

class AuthorData(AbstractData):
    """
    Data type to store author data.
    """
    tableName = "authors"
    tableColumns = AbstractData.tableColumns.copy()
    tableColumns.update({"first_name": "TEXT NOT NULL", "middle_name": "TEXT NOT NULL", "last_name": "TEXT NOT NULL", "birth_date": "TEXT", "death_date": "TEXT", "bio": "TEXT"})
    tableAddLines = []#["UNIQUE(first_name, middle_name, last_name)"]
    def __init__(self, name : str):
        # name is space separated string
        super().__init__()
        nameList = name.split(" ")
        self._firstName: str = nameList[0]
        if len(nameList) > 1:
            self._lastName: str = nameList[-1]
            self._middleNames: list[str] = nameList[1:-1]
        else:
            self._lastName: str = ""
            self._middleNames: list[str] = []
        self._affiliation: OrganizationData = None
        self._bio: str = None
        self._birthDate: QDate = None
        self._deathDate: QDate = None
        self._comment: str = None
        
    @property
    def firstName(self) -> str:
        return self._firstName

    @firstName.setter
    def firstName(self, value : str):
        self._firstName = value

    @property
    def lastName(self) -> str:
        return self._lastName

    @lastName.setter
    def lastName(self, value : str):
        self._lastName = value

    @property
    def middleNames(self) -> list[str]:
        return self._middleNames

    @middleNames.setter
    def middleNames(self, value : list[str]):
        self._middleNames = value

    @property
    def affiliation(self) -> OrganizationData:
        return self._affiliation

    @affiliation.setter
    def affiliation(self, value : OrganizationData):
        self._affiliation = value

    @property
    def bio(self) -> str:
        return self._bio

    @bio.setter
    def bio(self, value : str):
        self._bio = value

    @property
    def birthDate(self) -> QDate:
        return self._birthDate

    @birthDate.setter
    def birthDate(self, value : QDate):
        self._birthDate = value

    @property
    def deathDate(self) -> QDate:
        return self._deathDate

    @deathDate.setter
    def deathDate(self, value : QDate):
        self._deathDate = value
    
    @property
    def comment(self) -> str:
        return self._comment
    
    @comment.setter
    def comment(self, value : str):
        self._comment = value
        
    @classmethod
    def createEmptyInstance(cls) -> 'AuthorData':
        return AuthorData("")
    
    def getDataToInsert(self) -> dict[str, str]:
        data = super().getDataToInsert()
        data["first_name"] = self.firstName
        data["last_name"] = self.lastName
        data["middle_name"] = ' '.join(self.middleNames)
        data["birth_date"] = self.birthDate.toString(Qt.ISODate) if self.birthDate else None
        data["death_date"] = self.deathDate.toString(Qt.ISODate) if self.deathDate else None
        data["bio"] = self.bio
        return data
    
    def fillFromRow(self, row: list[str]) -> list[str]:
        nrow = super().fillFromRow(row)
        self.firstName = nrow[0]
        self.middleNames = nrow[1].split(" ")
        self.lastName = nrow[2]
        self.birthDate = QDate.fromString(nrow[3], Qt.ISODate) if nrow[3] else None
        self.deathDate = QDate.fromString(nrow[4], Qt.ISODate) if nrow[4] else None
        self.bio = nrow[5]  
        return nrow[6:]
    
    def toString(self):
        return ' '.join([self.firstName] + self.middleNames + [self.lastName])
    
    def toShortString(self):
        return ' '.join([self.firstName] + [self.lastName])
    
    def getDisplayData(self, field: str) -> str:
        if field == "firstName":
            return self.firstName
        elif field == "lastName":
            return self.lastName
        elif field == "middleNames":
            return ' '.join(self.middleNames)
        elif field == "affiliation":
            return self.affiliation.toString() or ""
        elif field == "bio":
            return self.bio or ""
        elif field == "birthDate":
            return self.birthDate.toString(Qt.ISODate) if self.birthDate else ""
        elif field == "deathDate":
            return self.deathDate.toString(Qt.ISODate) if self.deathDate else ""   
        elif field == "comment":
            return self.comment or ""   
        return super().getDisplayData(field)

class EntryData(AbstractData):
    """
    Abstract Data type to store entry data like articles, books, lecture notes, etc.
    createTable creates also additional tables to keep reference to authors.
    """    
    tableColumns = AbstractData.tableColumns.copy()
    tableColumns.update({"title": "TEXT NOT NULL", "summary": "TEXT", "file_name": "TEXT", "comment": "TEXT", "preview_page": "INTEGER DEFAULT 0"})
    def __init__(self, title : str, authors : list[AuthorData]):
        super().__init__()
        self._title: str = title
        self._authors: list[AuthorData] = authors
        self._fileName: str = None
        self._summary: str = None
        self._comment: str = None
        self._previewPage: int = 0
        
    @property
    def summary(self) -> str:
        return self._summary
    
    @summary.setter
    def summary(self, value : str):
        self._summary = value
        
    @property
    def fileName(self) -> str:
        return self._fileName
    
    @fileName.setter
    def fileName(self, value : str):
        self._fileName = value
        
    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value : str):
        self._title = value

    @property
    def authors(self) -> list[AuthorData]:
        return self._authors

    @authors.setter
    def authors(self, value : list[AuthorData]):
        self._authors = value
        
    @property
    def comment(self) -> str:
        return self._comment
    
    @comment.setter
    def comment(self, value : str):
        self._comment = value
        
    @property
    def previewPage(self) -> int:
        return self._previewPage
    @previewPage.setter
    def previewPage(self, value : int):
        self._previewPage = value
        
    @classmethod
    def createTable(cls, db : AMTDatabase) -> bool:
        if not super().createTable(db):
            return False
        query = AMTQuery(db)
        # create ref table to authors 
        if not query.createTable(f"{cls.tableName}_{AuthorData.tableName}", { f"{AuthorData.tableName}_id": "INTEGER NOT NULL", f"{cls.tableName}_id": "INTEGER NOT NULL"}):
            return False
        if not query.createTableAddLines([f"FOREIGN KEY ({AuthorData.tableName}_id) REFERENCES {AuthorData.tableName}(id) ON DELETE CASCADE", f"FOREIGN KEY ({cls.tableName}_id) REFERENCES {cls.tableName}(id) ON DELETE CASCADE"]):
            return False
        return query.exec()
        
    @classmethod
    def extractData(cls, db: AMTDatabase, filter: str = "") -> list[AbstractData]:
        entries = super().extractData(db, filter)
        #logger.debug(f"extracted {len(entries)} entries")
        query = AMTQuery(db)
        for entry in entries:
            refTable = f"{cls.tableName}_{AuthorData.tableName}"
            refId = f"{AuthorData.tableName}_id"
            query.selectByReference(AuthorData.tableName, refTable, "id", refId, columns=AuthorData.tableColumns.keys(), filter=f"{refTable}.{cls.tableName}_id = {entry.id}")
            query.exec()
            authors = []
            while query.next():
                authorRow = [query.value(i) for i in range(len(AuthorData.tableColumns))]
                author = AuthorData.fromRow(authorRow)
                authors.append(author)
                #logger.debug(f"extracted author {[author.firstName, author.lastName, author.middleNames]}")
            entry.authors = authors
        return entries
        
    def getDataToInsert(self) -> dict[str, str]:
        data = super().getDataToInsert()
        data["title"] = self.title
        data["summary"] = self.summary
        data["file_name"] = self.fileName
        data["comment"] = self.comment
        data["preview_page"] = str(self.previewPage)
        return data
    
    @classmethod
    def insertMultiple(cls : Type[T], db : AMTDatabase, data : list[T]) -> bool:
        if not super().insertMultiple(db, data):
            return False
        query = AMTQuery(db)    
        refTable = f"{cls.tableName}_{AuthorData.tableName}"
        refId = f"{cls.tableName}_id"
        refAuthorId = f"{AuthorData.tableName}_id"
        # insert authors
        authorsToInsert = [author for sublist in [d.authors for d in data] for author in sublist]
        if len(authorsToInsert) == 0:
            return True
        if not AuthorData.insertMultiple(db, authorsToInsert):
            return False
        # insert reference
        refsToInsert = []
        for entry in data:
            for author in entry.authors:
                refsToInsert.append({refAuthorId: str(author.id), refId: str(entry.id)})
        if not query.insert(refTable, refsToInsert):
            return False
        if not query.exec():
            return False
        return True
    
    def insert(self, db: AMTDatabase) -> bool:
        # if insertion of entry failed, do not insert authors and reference
        if not super().insert(db):
            return False
        # insert authors and reference
        query = AMTQuery(db)
        refTable = f"{self.tableName}_{AuthorData.tableName}"
        refId = f"{self.tableName}_id"
        refAuthorId = f"{AuthorData.tableName}_id"
        authorsToInsert = self.authors
        if len(authorsToInsert) == 0:
            return True
        if not AuthorData.insertMultiple(db, authorsToInsert):
            logger.error(f"Failed to insert authors")
            return False
        refsToInsert = []
        for author in self.authors:
            refsToInsert.append({refAuthorId: str(author.id), refId: str(self.id)})
        if not query.insert(refTable, refsToInsert):
            return False
        if not query.exec():
            return False
        return True
    
    def update(self, db: AMTDatabase) -> bool:
        if not super().update(db):
            return False
        # update authors and reference
        query = AMTQuery(db)
        refTable = f"{self.tableName}_{AuthorData.tableName}"
        refId = f"{self.tableName}_id"
        refAuthorId = f"{AuthorData.tableName}_id"
        # remove all references
        logger.debug(f"deleting references for {self.id}")
        if not query.delete(refTable, f"{refId} = {self.id}"):
            return False
        if not query.exec():
            return False
        # add new authors or ignore existing
        authorsToInsert = [author for author in self.authors if not author.id]
        if len(authorsToInsert) == 0:
            return True
        if not AuthorData.insertMultiple(db, authorsToInsert):
            logger.error(f"Failed to insert authors")
            return False
        refsToInsert = []
        for author in self.authors:
            refsToInsert.append({refAuthorId: str(author.id), refId: str(self.id)})
        if not query.insert(refTable, refsToInsert):
            return False
        if not query.exec():
            return False
        return True      
    
    def fillFromRow(self, row: list[str]) -> list[str]:
        nrow = super().fillFromRow(row)
        self.title = nrow[0]
        self.summary = nrow[1]
        self.fileName = nrow[2]
        self.comment = nrow[3]
        self.previewPage = int(nrow[4])
        return nrow[5:]
        
    def toString(self):
        s = ""
        for auth in self.authors[:-1]:
            s += auth.toShortString()
            s += ", "
        s += self.authors[-1].toShortString()
        s += " - "
        s += self.title
        return s
    
    def toShortString(self):
        return self.title
    
    def getAuthorsString(self):
        s = ""
        if isinstance(self.authors, list):
            s = ", ".join([auth.toShortString() for auth in self.authors])
        return s
    
    def getDisplayData(self, field : str) -> str:
        if field == "title":
            return self.title
        elif field == "authors":
            return self.getAuthorsString()
        elif field == "fileName":
            return self.fileName or ""
        elif field == "summary":
            return self.summary or ""
        elif field == "comment":
            return self.comment or ""
        elif field == "previewPage":
            return str(self.previewPage)
        return super().getDisplayData(field)
    
class PublishableData(EntryData):
    """
    Abstract Data type to store publishable data like articles, books, lecture notes, etc. that have DOI, link, date published.
    """
    tableColumns = EntryData.tableColumns.copy()
    tableColumns.update({"doi": "TEXT", "link": "TEXT", "date_published": "TEXT"})
    def __init__(self, title : str, authors : list[AuthorData]):
        super().__init__(title, authors)
        self._doi: str = None
        self._link: str = None
        self._datePublished: QDate = None
        
    @property
    def doi(self) -> str:
        return self._doi
    
    @doi.setter
    def doi(self, value : str):
        self._doi = value

    @property
    def link(self) -> str:
        return self._link
    
    @link.setter
    def link(self, value : str):
        self._link = value

    @property
    def datePublished(self) -> QDate:
        return self._datePublished
    
    @datePublished.setter
    def datePublished(self, value : QDate):
        self._datePublished = value
        
    def getDataToInsert(self) -> dict[str, str]:
        data = super().getDataToInsert()
        data["doi"] = self.doi
        data["link"] = self.link
        data["date_published"] = self.datePublished.toString(Qt.ISODate) if self.datePublished else None
        return data
        
    def fillFromRow(self, row: list[str]) -> list[str]:
        nrow = super().fillFromRow(row)
        self.doi = nrow[0]
        self.link = nrow[1]
        self.datePublished = QDate.fromString(nrow[2], Qt.ISODate) if nrow[2] else None
        return nrow[3:]
        
    def getDisplayData(self, field: str) -> str:
        if field == "doi":
            return self.doi or ""
        elif field == "link":
            return self.link or ""
        elif field == "datePublished":
            return self.datePublished.toString(Qt.ISODate) if self.datePublished else ""
        return super().getDisplayData(field)
        
class ArticleData(PublishableData):
    """
    Data type to store article data.
    """
    tableName = "articles"
    tableColumns = PublishableData.tableColumns.copy()
    tableColumns.update({"arxivid": "TEXT", "version": "TEXT", "journal": "TEXT", "date_arxiv_uploaded": "TEXT", "date_arxiv_updated": "TEXT", "prime_category": "TEXT"})  
    tableAddLines = [] #["UNIQUE(title, doi)"]
    def __init__(self, title : str, authors : list[AuthorData]):
        super().__init__(title, authors)
        self._arxivid : str = None
        self._version : str = None
        self._journal: str = None
        self._dateArxivUploaded: QDateTime = None
        self._dateArxivUpdated: QDateTime = None
        self._primeCategory: str = None
               
    @property
    def primeCategory(self) -> str:
        return self._primeCategory
    
    @primeCategory.setter
    def primeCategory(self, value : str):
        self._primeCategory = value

    @property
    def arxivid(self) -> str:
        return self._arxivid
    
    @arxivid.setter
    def arxivid(self, value : str):
        self._arxivid = value

    @property
    def version(self) -> int:
        return self._version
    
    @version.setter
    def version(self, value : int):
        self._version = value

    @property
    def journal(self) -> str:
        return self._journal
    
    @journal.setter
    def journal(self, value : str):
        self._journal = value

    @property
    def dateArxivUploaded(self) -> QDateTime:
        return self._dateArxivUploaded
    
    @dateArxivUploaded.setter
    def dateArxivUploaded(self, value : QDateTime):
        self._dateArxivUploaded = value

    @property
    def dateArxivUpdated(self) -> QDateTime:
        return self._dateArxivUpdated
    
    @dateArxivUpdated.setter
    def dateArxivUpdated(self, value : QDateTime):
        self._dateArxivUpdated = value
        
    @classmethod
    def createEmptyInstance(cls) -> 'ArticleData':
        return ArticleData("", [])
    
    def fillFromRow(self, row: list[str]) -> list[str]:
        nrow = super().fillFromRow(row)
        self.arxivid = nrow[0]
        self.version = nrow[1] if nrow[1] else None
        self.journal = nrow[2]
        self.dateArxivUploaded = QDateTime.fromString(nrow[3], Qt.ISODate) if nrow[3] else None
        self.dateArxivUpdated = QDateTime.fromString(nrow[4], Qt.ISODate) if nrow[4] else None
        self.primeCategory = nrow[5]
        return nrow[6:]
        
    def getDataToInsert(self) -> dict[str, str]:
        data = super().getDataToInsert()
        data["arxivid"] = self.arxivid
        data["version"] = self.version
        data["journal"] = self.journal
        data["date_arxiv_uploaded"] = self.dateArxivUploaded.toString(Qt.ISODate) if self.dateArxivUploaded else None
        data["date_arxiv_updated"] = self.dateArxivUpdated.toString(Qt.ISODate) if self.dateArxivUpdated else None
        data["prime_category"] = self.primeCategory
        data["summary"] = self.summary
        return data
                        
    def getDisplayData(self, field: str) -> str:
        if field == "arxivid":
            return self.arxivid  or ""
        elif field == "version":    
            return str(self.version) if self.version else ""
        elif field == "journal":
            return self.journal or ""
        elif field == "dateArxivUploaded":
            return self.dateArxivUploaded.toString(Qt.ISODate) if self.dateArxivUploaded else ""
        elif field == "dateArxivUpdated":
            return self.dateArxivUpdated.toString(Qt.ISODate) if self.dateArxivUpdated else ""
        elif field == "primeCategory":
            return self.primeCategory or ""
        return super().getDisplayData(field)
        
class BookData(PublishableData):
    """
    Data type to store book data.
    """
    tableName = "books"
    tableColumns = PublishableData.tableColumns.copy()
    tableColumns.update({"isbn": "TEXT", "publisher": "TEXT", "edition": "TEXT"})
    #tableColumns = {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "title": "TEXT NOT NULL", "doi": "TEXT", "link": "TEXT", "date_published": "TEXT", "isbn": "TEXT", "publisher": "TEXT", "edition": "TEXT", "summary": "TEXT", "file_name": "TEXT", "comment": "TEXT", "preview_page": "INTEGER DEFAULT 0"}
    tableAddLines = [] #["UNIQUE(title, doi, edition)"]
    def __init__(self, title : str, authors : list[AuthorData]):
        super().__init__(title, authors)
        self._isbn: str = None
        self._publisher: str = None
        self._edition: str = None

    @property
    def isbn(self) -> str:
        return self._isbn

    @isbn.setter
    def isbn(self, value: str):
        self._isbn = value

    @property
    def publisher(self) -> str:
        return self._publisher

    @publisher.setter
    def publisher(self, value: str):
        self._publisher = value

    @property
    def edition(self) -> str:
        return self._edition

    @edition.setter
    def edition(self, value: str):
        self._edition = value
        
    @classmethod
    def createEmptyInstance(cls) -> 'BookData':
        return BookData("", [])
    
    def fillFromRow(self, row: list[str]) -> list[str]:
        nrow = super().fillFromRow(row)
        self.isbn = nrow[0]
        self.publisher = nrow[1]
        self.edition = nrow[2]
        return nrow[3:]
    
    def getDataToInsert(self) -> dict[str, str]:
        data = super().getDataToInsert()
        data["isbn"] = self.isbn
        data["publisher"] = self.publisher
        data["edition"] = self.edition
        return data
    
    def getDisplayData(self, field: str) -> str:
        if field == "isbn":
            return self.isbn or ""
        elif field == "publisher":
            return self.publisher or ""
        elif field == "edition":
            return self.edition or ""
        return super().getDisplayData(field)

class LecturesData(PublishableData):
    """
    Data type to store lecture notes data.
    """
    tableName = "lectures"
    tableColumns= PublishableData.tableColumns.copy()
    tableColumns.update({"school": "TEXT", "course": "TEXT"})
    tableAddLines = [] #["UNIQUE(title, course, school)"]
    def __init__(self, title : str, authors : list[AuthorData]):
        super().__init__(title, authors)
        self._school: str = None
        self._course: str = None

    @property
    def course(self) -> str:
        return self._course

    @course.setter
    def course(self, value : str):
        self._course = value

    @property
    def school(self) -> str:
        return self._school

    @school.setter
    def school(self, value : str):
        self._school = value
        
    @classmethod
    def createEmptyInstance(cls) -> 'LecturesData':
        return LecturesData("", [])

    def fillFromRow(self, row: list[str]) -> list[str]:
        nrow = super().fillFromRow(row)
        self.school = nrow[0]
        self.course = nrow[1]
        return nrow[2:]
    
    def getDataToInsert(self) -> dict[str, str]:
        data = super().getDataToInsert()
        data["school"] = self.school
        data["course"] = self.course
        return data    
    
    def getDisplayData(self, field: str) -> str:
        if field == "school":
            return self.school or ""
        elif field == "course":
            return self.course or ""
        return super().getDisplayData(field)