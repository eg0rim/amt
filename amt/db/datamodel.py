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
from amt.db.database import AMTQuery
from amt.logger import getLogger

logger = getLogger(__name__)


class AbstractData(object):
    tableName: str = None
    tableColumns: list[str] = None
    
    def __init__(self):
        super().__init__()
        # id must be specified only to existing data in database
        # for new data it is must be None
        # insertion must assign id
        self._id: int = None
        self._comment: str = None
    
    @property
    def id(self) -> int:
        return self._id
    
    @id.setter
    def id(self, value : int):
        self._id = value
        
    @property
    def comment(self) -> str:
        return self._comment
    
    @comment.setter
    def comment(self, value : str):
        self._comment = value
    
    @classmethod
    def createTable(cls, query : AMTQuery) -> bool:
        return False
    
    def fromRow(self, row : list[str]) -> 'AbstractData':
        pass
    
    @classmethod 
    def extractData(cls, query : AMTQuery, filter : str) -> list['AbstractData']:
        return []
    
    def insert(self, query : AMTQuery) -> bool:
        if self.id is not None:
            logger.error("Cannot insert data with existing id")
            return False
    
    def delete(self, query : AMTQuery) -> bool:
        if not self.id:
            logger.error("Cannot delete data without id")
            return False
        queryString = f"DELETE FROM {self.tableName} WHERE {self.tableColumns[0]} = {self.id}"
        logger.debug(f"Deleting data: {queryString}")
        if not query.exec(queryString):
            logger.error(f"Failed to delete data")
            return False
        self.id = None
        return True
    
    def update(self, query : AMTQuery) -> bool:
        if not self.id:
            logger.error("Cannot update data without id")
            return False
        self.delete(query)
        self.insert(query)
        return True  
    
    def toString(self) -> str:
        pass
    
    def toShortString(self) -> str:
        pass
    
    def getDisplayData(self, field : str) -> str:
        if field == "id":
            return str(self.id) if self.id else ""
        elif field == "comment":
            return self.comment or ""
        elif field == "name":
            return self.toString() 
        elif field == "shortName":
            return self.toShortString()      
        return ""

class OrganizationData(AbstractData):
    """institute, university, company, etc data"""
    def __init__(self, orgName : str):
        super().__init__()
        self._name: str = orgName
        self._shortName: str = orgName
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
        
    def toString(self):
        return self.name or ""
    
    def toShortString(self):
        return self.shortName or ""
    
    def getDisplayData(self, field: str) -> str:
        if field == "address":
            return self.address or ""
        elif field == "info":
            return self.info
        return super().getDisplayData(field)
    

class AuthorData(AbstractData):
    """author data"""
    
    tableName = "authors"
    tableColumns = ["id", "first_name", "middle_name", "last_name", "birth_date", "death_date", "bio"]
    
    def __init__(self, name : str):
        # name is space separated string
        super().__init__()
        nameList = name.split(" ")
        self._firstName: str = nameList[0]
        if len(nameList) > 1:
            self._lastName: str = nameList[-1]
            self._middleNames: list[str] = nameList[1:-1]
        else:
            self._lastName: str = None
            self._middleNames: list[str] = None
        self._affiliation: OrganizationData = None
        self._bio: str = None
        self._birthDate: QDate = None
        self._deathDate: QDate = None
        
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
    
    @classmethod
    def createTable(cls, query : AMTQuery) -> bool:
        queryString = f"""
            CREATE TABLE IF NOT EXISTS {cls.tableName} (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT,
                middle_name TEXT,
                birth_date TEXT,
                death_date TEXT,
                bio TEXT,
                UNIQUE(first_name, last_name, birth_date)
            )
            """
        if not query.exec(queryString):
            logger.error(f"Failed to create table {cls.tableName}")
            return False
        else:
            return True
    
    @classmethod
    def fromRow(cls, row: list[str]) -> 'AuthorData':
        author = AuthorData(' '.join(row[1:4]))
        author.id = row[0]
        author.birthDate = QDate.fromString(row[4], Qt.ISODate) if row[4] else None
        author.deathDate = QDate.fromString(row[5], Qt.ISODate) if row[5] else None
        author.bio = row[6] 
        return author
        
    @classmethod
    def extractData(cls, query : AMTQuery, filter : str) -> list['AuthorData']:
        if not query.select(cls.tableName, cls.tableColumns, filter):
            return []
        authors = []
        while query.next():
            row = [query.value(i) for i in range(len(cls.tableColumns))]
            authors.append(cls.fromRow(row))
        return authors
    
    def insert(self, query : AMTQuery) -> bool:
        if not super().insert(query):
            return False
        dataToInsert = {
            "first_name": self.firstName, 
            "last_name": self.lastName,
            "middle_name": ' '.join(self.middleNames) if self.middleNames else None,
            "birth_date": self.birthDate.toString(Qt.ISODate) if self.birthDate else None,
            "death_date": self.deathDate.toString(Qt.ISODate) if self.deathDate else None,
            "bio": self.bio
        }
        queryStringFields = ", ".join(dataToInsert.keys())
        queryStringValues = ", ".join([f"'{value}'" if value is not None else "NULL" for value in dataToInsert.values()])
        queryString = f"INSERT INTO {self.tableName} ({queryStringFields}) VALUES ({queryStringValues})"
        logger.debug(f"Inserting author data: {queryString}")
        if not query.exec(queryString):
            logger.error(f"Failed to insert author data")
            return False
        # get id of the inserted author
        if not query.exec("SELECT last_insert_rowid()"):
            logger.error(f"Failed to get id of the inserted author")
            return False
        if not query.next():
            logger.error(f"Failed to get id of the inserted author")
            return False
        self.id = query.value(0)
        return True
    
    
    
    # update is implemented as delete and insert
    # def update(self, query : AMTQuery) -> bool:
    #     if not super().update(query):
    #         return False
    #     dataToUpdate = {
    #         "first_name": self.firstName, 
    #         "last_name": self.lastName,
    #         "middle_name": ' '.join(self.middleNames) if self.middleNames else None,
    #         "birth_date": self.birthDate.toString(Qt.ISODate) if self.birthDate else None,
    #         "death_date": self.deathDate.toString(Qt.ISODate) if self.deathDate else None,
    #         "bio": self.bio
    #     }
    #     queryStringFields = ", ".join([f"{key} = '{value}'" if value is not None else f"{key} = NULL" for key, value in dataToUpdate.items()])
    #     queryString = f"UPDATE {self.tableName} SET {queryStringFields} WHERE id = {self.id}"
    #     logger.debug(f"Updating author data: {queryString}")
    #     if not query.exec(queryString):
    #         logger.error(f"Failed to update author data")
    #         return False
    #     return True
            
    # def toString(self):
    #     return ' '.join([self.firstName] + self.middleNames + [self.lastName])
    
    # def toShortString(self):
    #     return ' '.join([self.firstName] + [self.lastName])
    
    def getDisplayData(self, field: str) -> str:
        if field == "firstName":
            return self.firstName or ""
        elif field == "lastName":
            return self.lastName or ""
        elif field == "middleNames":
            return ' '.join(self.middleNames) if self.middleNames else ""
        elif field == "affiliation":
            return self.affiliation.toString() or ""
        elif field == "bio":
            return self.bio or ""
        elif field == "birthDate":
            return self.birthDate.toString(Qt.ISODate) if self.birthDate else ""
        elif field == "deathDate":
            return self.deathDate.toString(Qt.ISODate) if self.deathDate else ""      
        return super().getDisplayData(field)

class EntryData(AbstractData):
    """entry data"""
    def __init__(self, title : str, authors : list[AuthorData]):
        super().__init__()
        self._title: str = title
        self._authors: list[AuthorData] = authors
        self._fileName: str = None
        self._summary: str = None
        
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
        if len(self.authors) > 0:
            s = ", ".join([auth.toShortString() for auth in self.authors])
        return s
    
    def getDisplayData(self, field : str) -> str:
        if field == "title":
            return self.toShortString()
        elif field == "authors":
            return self.getAuthorsString()
        elif field == "fileName":
            return self.fileName or ""
        elif field == "summary":
            return self.summary or ""
        return super().getDisplayData(field)
    
class PublishableData(EntryData):
    """publishable data"""
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
        
    def getDisplayData(self, field: str) -> str:
        if field == "doi":
            return self.doi
        elif field == "link":
            return self.link
        elif field == "datePublished":
            return self.datePublished.toString(Qt.ISODate) if self.datePublished else ""
        return super().getDisplayData(field)
        
class ArticleData(PublishableData):
    """article data"""
    tableName = "articles"
    tableColumns = ["id", "title", "doi", "link", "date_published", "arxivid", "version", "journal", "date_arxiv_uploaded", "date_arxiv_updated", "prime_category", "summary", "file_name", "comment"]
    
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
    def createTable(cls, query : AMTQuery) -> bool:
        queryString = f"""
            CREATE TABLE IF NOT EXISTS {cls.tableName} (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                doi TEXT UNIQUE,
                link TEXT,
                date_published TEXT,
                arxivid TEXT UNIQUE,
                version INTEGER,
                journal TEXT,
                date_arxiv_uploaded TEXT,
                date_arxiv_updated TEXT,
                prime_category TEXT,
                summary TEXT,
                file_name TEXT,
                comment TEXT
                UNIQUE(title, version, doi)
            )
            """
        if not query.exec(queryString):
            logger.error(f"Failed to create table {cls.tableName}")
            return False
        queryString = f"""
            CREATE TABLE IF NOT EXISTS {cls.tableName}_{AuthorData.tableName} (
                author_id INTEGER NOT NULL,
                article_id INTEGER NOT NULL,
                FOREIGN KEY (author_id) REFERENCES {AuthorData.tableName}(id) ON DELETE CASCADE,
                FOREIGN KEY (article_id) REFERENCES {cls.tableName}(id) ON DELETE CASCADE
                )
                """  
        if not query.exec(queryString):
            logger.error(f"Failed to create table {cls.tableName}_{AuthorData.tableName}")
            return False
        return True
    
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
        return article
    
    @classmethod   
    def extractData(cls, query : AMTQuery, filter : str) -> list['ArticleData']:
        if not query.select(cls.tableName, cls.tableColumns, filter):
            return []
        articles = []
        while query.next():
            row = [query.value(i) for i in range(len(cls.tableColumns))]
            article = cls.fromRow(row)
            # get authors
            refTable = f"{cls.tableName}_{AuthorData.tableName}"
            authorQuery = AMTQuery(query.db)
            authorQuery.selectByReference(AuthorData.tableName, refTable, "id", "author_id", filter=f"{refTable}.article_id = {article.id}")
            authors = []
            while authorQuery.next():
                authorRow = [authorQuery.value(i) for i in range(len(AuthorData.tableColumns))]
                author = AuthorData.fromRow(authorRow)
                authors.append(author)  
            article.authors = authors          
            articles.append(article)
        return articles
        
    def insert(self, query: AMTQuery) -> bool:
        if not super().insert(query):
            return False
        dataToInsert = {
            "title": self.title,
            "doi": self.doi,
            "link": self.link,
            "date_published": self.datePublished.toString(Qt.ISODate) if self.datePublished else None,
            "arxivid": self.arxivid,
            "version": self.version,
            "journal": self.journal,
            "date_arxiv_uploaded": self.dateArxivUploaded.toString(Qt.ISODate) if self.dateArxivUploaded else None,
            "date_arxiv_updated": self.dateArxivUpdated.toString(Qt.ISODate) if self.dateArxivUpdated else None,
            "prime_category": self.primeCategory,
            "summary": self.summary,
            "file_name": self.fileName,
            "comment": self.comment
        }
        queryStringFields = ", ".join(dataToInsert.keys())
        queryStringValues = ", ".join([f"'{value}'" if value is not None else "NULL" for value in dataToInsert.values()])
        queryString = f"INSERT INTO {self.tableName} ({queryStringFields}) VALUES ({queryStringValues})"
        logger.debug(f"Inserting article data: {queryString}")
        if not query.exec(queryString):
            logger.error(f"Failed to insert article data")
            return False
        # get id of the inserted article
        if not query.exec("SELECT last_insert_rowid()"):
            logger.error(f"Failed to get id of the inserted article")
            return False
        if not query.next():
            logger.error(f"Failed to get id of the inserted article")
            return False
        self.id = query.value(0)
        # insert authors
        refTable = f"{self.tableName}_{AuthorData.tableName}"
        for author in self.authors:
            author.insert(query)
            queryString = f"INSERT INTO {refTable} (author_id, article_id) VALUES ({author.id}, {self.id})"
            logger.debug(f"Inserting author-article reference: {queryString}")
            if not query.exec(queryString):
                logger.error(f"Failed to insert author-article reference")
                return False
        return True
                
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
    """books data"""
    tableName = "books"
    tableColumns = ["id", "title", "doi", "link", "date_published", "isbn", "publisher", "edition", "summary", "file_name", "comment"]
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
    def createTable(cls, query : AMTQuery) -> bool:
        queryString = f"""
            CREATE TABLE IF NOT EXISTS {cls.tableName} (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                doi TEXT UNIQUE,
                link TEXT,
                date_published TEXT,
                isbn TEXT UNIQUE,
                publisher TEXT,
                edition TEXT,
                summary TEXT,
                file_name TEXT,
                comment TEXT,
                UNIQUE(title, edition, doi)
            )
            """
        if not query.exec(queryString):
            logger.error(f"Failed to create table {cls.tableName}")
            return False
        # reference table
        queryString = f"""
            CREATE TABLE IF NOT EXISTS {cls.tableName}_{AuthorData.tableName} (
                author_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                FOREIGN KEY (author_id) REFERENCES {AuthorData.tableName}(id) ON DELETE CASCADE,
                FOREIGN KEY (book_id) REFERENCES {cls.tableName}(id) ON DELETE CASCADE
                )
                """
        if not query.exec(queryString):
            logger.error(f"Failed to create table {cls.tableName}_{AuthorData.tableName}")
            return False
        return True
        
    @classmethod
    def fromRow(cls, row: list[str]) -> 'BookData':
        book = BookData(row[1], [])
        book.id = row[0]
        book.doi = row[2]
        book.link = row[3]
        book.datePublished = QDate.fromString(row[4], Qt.ISODate)  if row[4] else None
        book.isbn = row[5]
        book.publisher = row[6]
        book.edition = row[7]
        book.summary = row[8]
        book.fileName = row[9]
        book.comment = row[10]
        return book
    
    @classmethod
    def extractData(cls, query : AMTQuery, filter : str) -> list['BookData']:
        if not query.select(cls.tableName, cls.tableColumns, filter):
            return []
        books = []
        while query.next():
            row = [query.value(i) for i in range(len(cls.tableColumns))]
            book = cls.fromRow(row)
            # get authors
            refTable = f"{cls.tableName}_{AuthorData.tableName}"
            authorQuery = AMTQuery(query.db)
            authorQuery.selectByReference(AuthorData.tableName, refTable, "id", "author_id", filter=f"{refTable}.book_id = {book.id}")
            authors = []
            while authorQuery.next():
                authorRow = [authorQuery.value(i) for i in range(len(AuthorData.tableColumns))]
                author = AuthorData.fromRow(authorRow)
                authors.append(author)  
            book.authors = authors          
            books.append(book)
        return books
    
    def insert(self, query : AMTQuery) -> bool:
        if not super().insert(query):
            return False
        dataToInsert = {
            "title": self.title,
            "doi": self.doi,
            "link": self.link,
            "date_published": self.datePublished.toString(Qt.ISODate) if self.datePublished else None,
            "isbn": self.isbn,
            "publisher": self.publisher,
            "edition": self.edition,
            "summary": self.summary,
            "file_name": self.fileName,
            "comment": self.comment
        }
        queryStringFields = ", ".join(dataToInsert.keys())
        queryStringValues = ", ".join([f"'{value}'" if value is not None else "NULL" for value in dataToInsert.values()])
        queryString = f"INSERT INTO {self.tableName} ({queryStringFields}) VALUES ({queryStringValues})"
        logger.debug(f"Inserting book data: {queryString}")
        if not query.exec(queryString):
            logger.error(f"Failed to insert book data")
            return False
        # get id of the inserted book
        if not query.exec("SELECT last_insert_rowid()"):
            logger.error(f"Failed to get id of the inserted book")
            return False
        if not query.next():
            logger.error(f"Failed to get id of the inserted book")
            return False
        self.id = query.value(0)
        # insert authors
        refTable = f"{self.tableName}_{AuthorData.tableName}"
        for author in self.authors:
            author.insert(query)
            queryString = f"INSERT INTO {refTable} (author_id, book_id) VALUES ({author.id}, {self.id})"
            logger.debug(f"Inserting author-book reference: {queryString}")
            if not query.exec(queryString):
                logger.error(f"Failed to insert author-book reference")
                return False
        return True
    
    def getDisplayData(self, field: str) -> str:
        if field == "isbn":
            return self.isbn or ""
        elif field == "publisher":
            return self.publisher or ""
        elif field == "edition":
            return self.edition or ""
        return super().getDisplayData(field)
 
        
class LecturesData(PublishableData):
    """lecture notes data"""
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
    def createTable(cls, query : AMTQuery) -> bool:
        queryString = f"""
            CREATE TABLE IF NOT EXISTS {cls.tableName} (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                doi TEXT UNIQUE,
                link TEXT,
                date_published TEXT,
                school TEXT,
                course TEXT,
                summary TEXT,
                file_name TEXT,
                comment TEXT,
                UNIQUE(title, course, school)
            )
            """
        if not query.exec(queryString):
            logger.error(f"Failed to create table {cls.tableName}")
            return False
        # reference table
        queryString = f"""
            CREATE TABLE IF NOT EXISTS {cls.tableName}_{AuthorData.tableName} (
                author_id INTEGER NOT NULL,
                lecture_id INTEGER NOT NULL,
                FOREIGN KEY (author_id) REFERENCES {AuthorData.tableName}(id) ON DELETE CASCADE,
                FOREIGN KEY (lecture_id) REFERENCES {cls.tableName}(id) ON DELETE CASCADE
                )
                """
        if not query.exec(queryString):
            logger.error(f"Failed to create table {cls.tableName}_{AuthorData.tableName}")
            return False
        return True
    
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
        return lecture
    
    @classmethod
    def extractData(cls, query : AMTQuery, filter : str) -> list['LecturesData']:
        if not query.select(cls.tableName, cls.tableColumns, filter):
            return []
        lectures = []
        while query.next():
            row = [query.value(i) for i in range(len(cls.tableColumns))]
            lecture = cls.fromRow(row)
            # get authors
            refTable = f"{cls.tableName}_{AuthorData.tableName}"
            authorQuery = AMTQuery(query.db)
            authorQuery.selectByReference(AuthorData.tableName, refTable, "id", "author_id", filter=f"{refTable}.lecture_id = {lecture.id}")
            authors = []
            while authorQuery.next():
                authorRow = [authorQuery.value(i) for i in range(len(AuthorData.tableColumns))]
                author = AuthorData.fromRow(authorRow)
                authors.append(author)  
            lecture.authors = authors          
            lectures.append(lecture)
        return lectures

    def insert(self, query : AMTQuery) -> bool:
        if not super().insert(query):
            return False
        dataToInsert = {
            "title": self.title,
            "doi": self.doi,
            "link": self.link,
            "date_published": self.datePublished.toString(Qt.ISODate) if self.datePublished else None,
            "school": self.school,
            "course": self.course,
            "summary": self.summary,
            "file_name": self.fileName,
            "comment": self.comment
        }
        queryStringFields = ", ".join(dataToInsert.keys())
        queryStringValues = ", ".join([f"'{value}'" if value is not None else "NULL" for value in dataToInsert.values()])
        queryString = f"INSERT INTO {self.tableName} ({queryStringFields}) VALUES ({queryStringValues})"
        logger.debug(f"Inserting lecture data: {queryString}")
        if not query.exec(queryString):
            logger.error(f"Failed to insert lecture data")
            return False
        # get id of the inserted lecture
        if not query.exec("SELECT last_insert_rowid()"):
            logger.error(f"Failed to get id of the inserted lecture")
            return False
        if not query.next():
            logger.error(f"Failed to get id of the inserted lecture")
            return False
        self.id = query.value(0)
        # insert authors
        refTable = f"{self.tableName}_{AuthorData.tableName}"
        for author in self.authors:
            author.insert(query)
            queryString = f"INSERT INTO {refTable} (author_id, lecture_id) VALUES ({author.id}, {self.id})"
            logger.debug(f"Inserting author-lecture reference: {queryString}")
            if not query.exec(queryString):
                logger.error(f"Failed to insert author-lecture reference")
                return False
        return True
    
    def getDisplayData(self, field: str) -> str:
        if field == "school":
            return self.school or ""
        elif field == "course":
            return self.course or ""
        return super().getDisplayData(field)