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

from PySide6.QtCore import (
    QDate,
    QDateTime,
    Qt
)
import subprocess
from amt.db.database import AMTDatabase, AMTQuery
from amt.logger import getLogger

logger = getLogger(__name__)


class AbstractData(object):
    """
    Abstract class for data storage and its insertion, deletion, update, etc. to specified database.
    Class attributes: 
        tableName: str - table name corresponding to the data type. Must be specified in subclasses
        tableColumns: dict[str, str] - table columns must be specified in the order of their appearance in the table with type and constraints. Must be specified in subclasses
        tableAddLines: list[str] - additional lines needed for create query. 
    Properties:
        id: int - id of the data. Must be specified only to existing data in database. For new data it is must be None. Insertion must assign id.
    Methods:
        createTable(db: AMTDatabase) -> bool
        select(db: AMTDatabase, filter: str = "") -> bool
        getDataToInsert() -> dict[str, str]
        insert(db: AMTDatabase) -> bool
        delete(db: AMTDatabase) -> bool
        update(db: AMTDatabase) -> bool
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
    tableColumns: dict[str, str] = None
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
    def createTable(cls, db : AMTDatabase) -> bool:
        """ 
        Create table in the database corresponding to the data type.
        Args:
            db (AMTDatabase): database object
        Returns:
            bool: True if table created successfully, False otherwise
        """
        query = AMTQuery(db)
        if not query.createTable(cls.tableName, cls.tableColumns): #, addLines=cls.tableAddLines):
            return False
        return query.exec()
    
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
    
    @classmethod
    def fromRow(cls, row : list[str]) -> 'AbstractData':
        """
        Create data object from row returned by select query.
        Must be implemented in subclasses.

        Args:
            row (list[str]): row returned by select query

        Returns:
            AbstractData: data object
        """
        pass
    
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
    tableColumns = {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "name": "TEXT NOT NULL", "short_name": "TEXT", "address": "TEXT", "info": "TEXT"}
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
        
    def getDataToInsert(self) -> dict[str, str]:
        data = super().getDataToInsert()
        data["name"] = self.name
        data["short_name"] = self.shortName
        data["address"] = self.address
        data["info"] = self.info
        return data
    
    @classmethod
    def fromRow(cls, row: list[str]) -> 'OrganizationData':
        org = OrganizationData(row[1])
        org.id = row[0]
        org.shortName = row[2]
        org.address = row[3]
        org.info = row[4]
        return org
        
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
    tableColumns = {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "first_name": "TEXT NOT NULL", "middle_name": "TEXT NOT NULL", "last_name": "TEXT NOT NULL", "birth_date": "TEXT", "death_date": "TEXT", "bio": "TEXT"}
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
        
    def getDataToInsert(self) -> dict[str, str]:
        data = super().getDataToInsert()
        data["first_name"] = self.firstName
        data["last_name"] = self.lastName
        data["middle_name"] = ' '.join(self.middleNames)
        data["birth_date"] = self.birthDate.toString(Qt.ISODate) if self.birthDate else None
        data["death_date"] = self.deathDate.toString(Qt.ISODate) if self.deathDate else None
        data["bio"] = self.bio
        return data
    
    @classmethod
    def fromRow(cls, row: list[str]) -> 'AuthorData':
        author = AuthorData(' '.join(row[1:4]))
        author.id = row[0]
        author.birthDate = QDate.fromString(row[4], Qt.ISODate) if row[4] else None
        author.deathDate = QDate.fromString(row[5], Qt.ISODate) if row[5] else None
        author.bio = row[6] 
        return author
    
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
    
    def insert(self, db: AMTDatabase) -> bool:
        # if insertion of entry failed, do not insert authors and reference
        if not super().insert(db):
            return False
        # insert authors and reference
        state = True # becomes False if any insertion fails of authors or reference
        query = AMTQuery(db)
        refTable = f"{self.tableName}_{AuthorData.tableName}"
        refId = f"{self.tableName}_id"
        refAuthorId = f"{AuthorData.tableName}_id"
        for author in self.authors:
            if not author.insert(db):
                logger.error(f"Failed to insert author")
                state = False
                # do not insert reference if author insertion failed
                continue
            query.insert(refTable, {refAuthorId: str(author.id), refId: str(self.id)})
            if not query.exec():
                logger.error(f"Failed to insert author-entry reference")
                state = False
        return state
        
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
    tableColumns = {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "title": "TEXT NOT NULL", "doi": "TEXT", "link": "TEXT", "date_published": "TEXT", "arxivid": "TEXT", "version": "INTEGER", "journal": "TEXT", "date_arxiv_uploaded": "TEXT", "date_arxiv_updated": "TEXT", "prime_category": "TEXT", "summary": "TEXT", "file_name": "TEXT", "comment": "TEXT", "preview_page": "INTEGER DEFAULT 0"}    
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
    def fromRow(cls, row: list[str]) -> 'ArticleData':
        article = ArticleData(row[1], [])
        article.id = row[0]
        article.doi = row[2]
        article.link = row[3]
        article.datePublished = QDate.fromString(row[4], Qt.ISODate) if row[4] else None
        article.arxivid = row[5]
        article.version = row[6]
        article.journal = row[7]
        article.dateArxivUploaded = QDateTime.fromString(row[8], Qt.ISODate)  if row[8] else None
        article.dateArxivUpdated = QDateTime.fromString(row[9], Qt.ISODate)  if row[9] else None
        article.primeCategory = row[10]
        article.summary = row[11]
        article.fileName = row[12]
        article.comment = row[13]
        article.previewPage = int(row[14])
        return article
        
    def getDataToInsert(self) -> dict[str, str]:
        data = super().getDataToInsert()
        data["arxivid"] = self.arxivid
        data["version"] = str(self.version) if self.version else None
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
    tableColumns = {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "title": "TEXT NOT NULL", "doi": "TEXT", "link": "TEXT", "date_published": "TEXT", "isbn": "TEXT", "publisher": "TEXT", "edition": "TEXT", "summary": "TEXT", "file_name": "TEXT", "comment": "TEXT", "preview_page": "INTEGER DEFAULT 0"}
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
    def fromRow(cls, row: list[str]) -> 'BookData':
        book = BookData(row[1], [])
        book.id = row[0]
        book.doi = row[2]
        book.link = row[3]
        book.datePublished = QDate.fromString(row[4], Qt.ISODate) if row[4] else None
        book.isbn = row[5]
        book.publisher = row[6]
        book.edition = row[7]
        book.summary = row[8]
        book.fileName = row[9]
        book.comment = row[10]
        book.previewPage = int(row[11])
        return book
    
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
    tableColumns = {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "title": "TEXT NOT NULL", "doi": "TEXT", "link": "TEXT", "date_published": "TEXT", "school": "TEXT", "course": "TEXT", "summary": "TEXT", "file_name": "TEXT", "comment": "TEXT", "preview_page": "INTEGER DEFAULT 0"}
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
    def fromRow(cls, row: list[str]) -> 'LecturesData':
        lecture = LecturesData(row[1], [])
        lecture.id = row[0]
        lecture.doi = row[2]
        lecture.link = row[3]
        lecture.datePublished = QDate.fromString(row[4], Qt.ISODate) if row[4] else None
        lecture.school = row[5]
        lecture.course = row[6]
        lecture.summary = row[7]
        lecture.fileName = row[8]
        lecture.comment = row[9]
        lecture.previewPage = int(row[10])
        return lecture
    
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