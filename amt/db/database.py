# -*- coding: utf-8 -*-
# amt/db/database.py

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

"""initialize and create connection to the database"""

from PySide6.QtSql import (
    QSqlDatabase, 
    QSqlQuery,
)
from PySide6.QtCore import Qt, QDateTime, QDate
from .datamodel import (
    AbstractData,
    AuthorData,
    ArticleData,
    LecturesData,
    BookData
)
from amt.logger import getLogger

logger = getLogger(__name__)

class AMTDatabaseError(Exception):
    def __init__(self, *args: object) -> None:
        """Class of database errors"""
        super().__init__(*args)

class AMTDatabase(QSqlDatabase):
    def __init__(self, databaseFile : str, *args : object) -> None:
        """Inherits QSqlDatabase. Creates database for AMT.
        
        :param str databaseFile: path to the database file
        :raises DatabaseEroor: if the connection to the database can not be established
        """
        super().__init__("QSQLITE", *args)
        self.setDatabaseName(databaseFile)
        # if not self.open():
        #     errormsg=self.lastError().text()
        #     logger.error(errormsg)
        #     raise AMTDatabaseError(errormsg)
        # self._createTables()

    def open(self):
        if not super().open():
            errormsg=self.lastError().text()
            logger.critical(f"db open error: {errormsg}")
            raise AMTDatabaseError(errormsg)
        self._createDefaultTables()

    def _createDefaultTables(self) -> None:
        """Create all necessary tables in the database."""
        query = QSqlQuery(self)
        query.exec(
            """
            CREATE TABLE IF NOT EXISTS author (
                author_id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                first_name VARCHAR NOT NULL,
                last_name VARCHAR,
                middle_name VARCHAR,
                UNIQUE(first_name, last_name, middle_name)
            )
            """
        )
        query.exec(
            """
            CREATE TABLE IF NOT EXISTS article (
                article_id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                title VARCHAR NOT NULL,
                arxiv_id VARCHAR,
                version INTEGER,
                date_uploaded VARCHAR,
                date_updated VARCHAR,
                comment VARCHAR,
                link VARCHAR,
                p_category VARCHAR,
                doi VARCHAR,
                journal VARCHAR,
                date_published VARCHAR,
                summary VARCHAR,
                filename VARCHAR,
                UNIQUE(title, version)
            )
            """
        )
        query.exec(
            """
            CREATE TABLE IF NOT EXISTS book (
                book_id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                title VARCHAR NOT NULL,
                edition INTEGER,
                comment VARCHAR,
                link VARCHAR,
                doi VARCHAR,
                publisher VARCHAR,
                date_published VARCHAR,
                summary VARCHAR,
                filename VARCHAR,
                UNIQUE(title, edition)
            )
            """
        )
        query.exec(
            """
            CREATE TABLE IF NOT EXISTS lectures (
                lectures_id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                title VARCHAR NOT NULL,
                course VARCHAR,
                school INTEGER,
                comment VARCHAR,
                link VARCHAR,
                doi VARCHAR,
                date_published VARCHAR,
                summary VARCHAR,
                filename VARCHAR,
                UNIQUE(title, course, school)
            )
            """
        )
        query.exec(
            """
            CREATE TABLE IF NOT EXISTS article_author (
                author_id INTEGER,
                article_id INTEGER,
                FOREIGN KEY (author_id) REFERENCES author(author_id),
                FOREIGN KEY (article_id) REFERENCES article(article_id)
            )
            """
        )
        query.exec(
            """
            CREATE TABLE IF NOT EXISTS book_author (
                author_id INTEGER,
                book_id INTEGER,
                FOREIGN KEY (author_id) REFERENCES author(author_id),
                FOREIGN KEY (book_id) REFERENCES book(book_id)
            )
            """
        )
        query.exec(
            """
            CREATE TABLE IF NOT EXISTS lectures_author (
                author_id INTEGER,
                lectures_id INTEGER,
                FOREIGN KEY (author_id) REFERENCES author(author_id),
                FOREIGN KEY (lectures_id) REFERENCES lectures(lectures_id)
            )
            """
        )
        query.exec(
            """
            CREATE TABLE IF NOT EXISTS arxivcategory (
                category VARCHAR UNIQUE NOT NULL
            )
            """
        )
        query.exec(
            """
            CREATE TABLE IF NOT EXISTS article_arxivcategory (
                category VARCHAR,
                article_id INTEGER,
                FOREIGN KEY (category) REFERENCES arxivcategory(category),
                FOREIGN KEY (article_id) REFERENCES article(article_id)
            )
            """
        )      
         
class AMTQuery(QSqlQuery):
    def __init__(self, db : AMTDatabase):
        super().__init__(db)
        self.db = db
        
    def select(self, table : str, columns : list[str] = [], filter : str = "") -> bool:
        """
        Implements query:
            SELECT table.columns FROM table WHERE filter

        Args:
            table (str): table to select from
            columns (list[str], optional): list of columns to select. Defaults to []: select all
            filter (str, optional): Defaults to "".

        Returns:
            bool: _description_
        """
        queryString = "SELECT "
        if columns:
            for col in columns[:-1]:
                queryString += f"{table}.{col}, "
            queryString += f"{table}.{col} "
        else:
            queryString += "* "
        queryString += f"FROM {table}"
        if filter:
            queryString += f" WHERE {filter}"
        logger.info(f"select {table} from db")
        if self.exec(queryString):
            logger.info(f"selection successful")
            return True
        else:
            logger.error("selection failed: " + self.query.lastError().text())
            return False
    
    def selectByReference(self, table : str, refTable : str, id : str, refid : str, columns : list[str] = [], filter : str = "") -> bool:
        """
        Implements query:
            SELECT table.columns FROM table JOIN refTable ON table.id = refTable.refid WHERE filter

        Args:
            table (str): table to select from
            refTable (str): reference table
            id (str): identifier column in table
            refid (str): corresponding reference column in ref table
            columns (list[str], optional): columns to select. Defaults to []: select all columns
            filter (str, optional): Defaults to "".

        Returns:
            bool: returns True if selection is successful
        """
        queryString = "SELECT "
        if columns:
            for col in columns[:-1]:
                queryString += f"{table}.{col}, "
            queryString += f"{table}.{col} "
        else:
            queryString += "* "
        queryString += f"FROM {table} JOIN {refTable} ON {table}.{id} = {refTable}.{refid}"
        if filter:
            queryString += f" WHERE {filter}"
        if self.exec(queryString):
            return True
        else:
            logger.error("selection failed: " + self.query.lastError().text())
            return False
        
    def amtData(self, typ : str) -> AbstractData:
        """
        returns a child of AbstractData (depending on typ) for the current record. If conversion is not possible, returns None
        
        Args:
            typ (str): type of data to return. Allowed values: author, article, lectures, book

        Returns:
            AbstractData: a child of AbstractData or None
        """
        logger.info(f"getting {typ} data")
        if not typ in ("article", "book", "lectures", "author"):
            logger.critical("amtData conversion error: encountered unexpected type")
            return None
        if typ == "author":
            fname = self.value("first_name")
            if fname is None:
                logger.error("first_name field was not found or Null")
                return None
            lname = self.value("last_name")
            if lname is None:
                lname = ""
            mnames = self.value("middle_name")
            if mnames is None:
                mnames = ""
            author = AuthorData(' '.join([fname, mnames, lname]))
            author.id = self.value("author_id")
            # TODO: fill other fields
            return author
        else:
            idstr = typ + "_id"
            reftab = typ + "_author"
            id = self.value(idstr)
            title = self.value("title")
            if title is None:
                logger.error("title field was not found or Null")
                return None
            newQuery = self.__class__(self.db)
            newQuery.selectByReference("author", reftab, "author_id", "author_id", filter=f"{idstr} = {id}")
            authors = []
            while newQuery.next():
                author = newQuery.amtData("author")
                if author:
                    authors.append(author)
                else:
                    logger.warning(f"invalid author encountered in row {newQuery.value(0)}")
            if typ == "article":
                entry =  ArticleData(title, authors)
                entry.id = self.value("article_id")
                entry.arxivid = self.value("arxiv_id")
            if typ == "book":
                entry =  BookData(title, authors)
                entry.id = self.value("book_id")
            if typ == "lectures":
                entry =  LecturesData(title, authors)
                entry.id = self.value("lectures_id")
            # TODO: fill other fields
            return entry
        
    def insert(self, table : str, entry : object) -> bool:
        """
        Implements query:
            INSERT INTO table (columns) VALUES (values)

        Args:
            table (str): table to insert into
            entry (AbstractData): data to insert

        Returns:
            bool: returns True if insertion is successful
        """
        if table == "author":
            if not isinstance(entry, AuthorData):
                logger.error("insertion failed: invalid data type")
                return False
            fieldsToInsert = ["first_name", "last_name", "middle_name"]
            valuesToInsert = [entry.firstName, entry.lastName, ' '.join(entry.middleNames)]
        elif table == "article":
            if not isinstance(entry, ArticleData):
                logger.error("insertion failed: invalid data type")
                return False
            fieldsToInsert = ["title", "arxiv_id", "version", "date_uploaded", "date_updated", "comment", "link", "p_category", "doi", "journal", "date_published", "summary", "filename"]
            valuesToInsert = [entry.title, entry.arxivid, entry.version, entry.dateArxivUploaded, entry.dateArxivUpdated, entry.comment, entry.link, entry.primeCategory, entry.doi, entry.journal, entry.datePublished, entry.summary, entry.fileName]
        elif table == "book":
            if not isinstance(entry, BookData):
                logger.error("insertion failed: invalid data type")
                return False
            fieldsToInsert = ["title", "edition", "comment", "link", "doi", "publisher", "date_published", "summary", "filename"]
            valuesToInsert = [entry.title, entry.edition, entry.comment, entry.link, entry.doi, entry.publisher, entry.datePublished, entry.summary, entry.fileName]
        elif table == "lectures":
            if not isinstance(entry, LecturesData):
                logger.error("insertion failed: invalid data type")
                return False
            fieldsToInsert = ["title", "course", "school", "comment", "link", "doi", "date_published", "summary", "filename"]
            valuesToInsert = [entry.title, entry.course, entry.school, entry.comment, entry.link, entry.doi, entry.datePublished, entry.summary, entry.fileName]
        elif table == "arxivcategory":
            if not isinstance(entry, dict):
                logger.error("insertion failed: invalid data type")
                return False
            fieldsToInsert = ["category"]
            valuesToInsert = [entry["category"]]
        elif table == "article_arxivcategory":
            if not isinstance(entry, dict):
                logger.error("insertion failed: invalid data type")
                return False
            fieldsToInsert = ["category", "article_id"]
            valuesToInsert = [entry["category"], entry["article_id"]]
        elif table in ("article_author", "book_author", "lectures_author"):
            if not isinstance(entry, dict):
                logger.error("insertion failed: invalid data type")
                return False
            fieldsToInsert = ["author_id", f"{table.split('_')[0]}_id"]
            valuesToInsert = [entry["author_id"], entry[f"{table.split('_')[0]}_id"]]
        queryStringFields = ""
        queryStringValues = ""
        for i in range(len(valuesToInsert)):
            if valuesToInsert[i] is None:
                continue
            if isinstance(valuesToInsert[i], QDate):
                valuesToInsert[i] = valuesToInsert[i].toString(Qt.ISODate)
            if isinstance(valuesToInsert[i], QDateTime):
                valuesToInsert[i] = valuesToInsert[i].toString(Qt.ISODateTime)
            queryStringFields += fieldsToInsert[i] + ", "
            queryStringValues += f"'{valuesToInsert[i]}', "
        queryStringFields = queryStringFields[:-2]
        queryStringValues = queryStringValues[:-2]
        queryString = f"INSERT OR IGNORE INTO {table} ({queryStringFields}) VALUES ({queryStringValues})"
        logger.debug(f"query to be executed: {queryString}")
        if True: #self.exec(queryString):
            return True
            
    # def insert(self, table: str, data: dict) -> bool:
    #     """inserts rows into a table
        
    #     :param str table: name of the table where insert rows to
    #     :param dist data: dictionary of the form {col1 : [val1_1, val1_2, ...], col2 : [val2_1, val2_2, ...], ...} results in WHERE col1 IN (val1_1, val2_2, ...) AND col2 IN (val2_1, val2_2, ...) AND ...
    #     :return: True if the insertion is sucessful
    #     :rtype: bool
    #     """
    #     dataValues = list(data.values())
    #     dataColumns = list(data.keys())
    #     #print(dataValues)
    #     if not DB._isRectangular(dataValues):
    #         logging.error("the data passed into insert is not consistent")
    #         return False
    #     queryString = "INSERT OR IGNORE INTO arg1 arg2 VALUES arg3"
    #     queryString = queryString.replace("arg1", table)
    #     queryString = queryString.replace("arg2", str(dataColumns).replace("[","(").replace("]",")") )
    #     arg3 = str(self._transpose(dataValues))[1:-1].replace("[","(").replace("]",")")
    #     queryString = queryString.replace("arg3", arg3)
    #     #print(queryString)
    #     if self.query.exec(queryString): 
    #         return True
    #     else: 
    #         logging.error("insertion failed: " + self.query.lastError().text())
    #         return False

    # def delete(self, table: str, data: dict) -> bool:
    #     """removes row(s) from a table
        
    #     :param str table: table to modify
    #     :param dict data: dictionary that has column names as keys and values corresponding to the row(s) to remove
    #     :return: True if the removal is succesful
    #     :rtype: bool
    #     """
    #     queryString = "DELETE FROM arg1 WHERE arg2"
    #     queryString = queryString.replace("arg1", table)
    #     condsString = ""
    #     for key in data.keys():
    #         condsString += str(key) +" IN " + str(data[key]).replace("[","(").replace("]",") AND ")
    #     condsString = condsString[0:-4]
    #     queryString = queryString.replace("arg2", condsString)
    #     print(queryString)
    #     if self.query.exec(queryString): 
    #         return True
    #     else: 
    #         logging.error("deletion failed: " + self.query.lastError().text())
    #         return False
    


    # @staticmethod
    # def _transpose(l: list) -> list:
    #     """transopose a list of lists
        
    #     :param list l: list to be transposed
    #     :return: transposed list
    #     :rtype: list
    #     """
    #     if type(l[0]) == list:
    #         return list(map(list, zip(*l )))  
    #     else: 
    #         return [l]

    # @staticmethod    
    # def _isRectangular(n: list) -> bool:
    #     """check whether a list of list is rectangular
        
    #     :param list n: list of lists
    #     :return: True if the list of list rectangular
    #     :rtype: bool
    #     """
    #     if type(n[0]) == list: 
    #         return all(len(i) == len(n[0]) for i in n)
    #     else:
    #         return True
        
