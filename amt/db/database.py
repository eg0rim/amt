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
        # allow foreign keys
        query.exec("PRAGMA foreign_keys = ON")
        query.exec(
            """
            CREATE TABLE IF NOT EXISTS author (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
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
                FOREIGN KEY (author_id) REFERENCES author(id) ON DELETE CASCADE,
                FOREIGN KEY (article_id) REFERENCES article(id) ON DELETE CASCADE
            )
            """
        )
        query.exec(
            """
            CREATE TABLE IF NOT EXISTS book_author (
                author_id INTEGER,
                book_id INTEGER,
                FOREIGN KEY (author_id) REFERENCES author(id) ON DELETE CASCADE,
                FOREIGN KEY (book_id) REFERENCES book(id) ON DELETE CASCADE
            )
            """
        )
        query.exec(
            """
            CREATE TABLE IF NOT EXISTS lectures_author (
                author_id INTEGER,
                lectures_id INTEGER,
                FOREIGN KEY (author_id) REFERENCES author(id) ON DELETE CASCADE,
                FOREIGN KEY (lectures_id) REFERENCES lectures(id) ON DELETE CASCADE
            )
            """
        )
        query.exec(
            """
            CREATE TABLE IF NOT EXISTS arxivcategory (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                category VARCHAR UNIQUE NOT NULL
            )
            """
        )
        query.exec(
            """
            CREATE TABLE IF NOT EXISTS article_arxivcategory (
                category_id VARCHAR,
                article_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES arxivcategory(id) ON DELETE CASCADE,
                FOREIGN KEY (article_id) REFERENCES article(id) ON DELETE CASCADE
            )
            """
        )      
         
class AMTQuery(QSqlQuery):
    def __init__(self, db : AMTDatabase):
        super().__init__(db)
        self.db = db
        
    def exec(self, queryString : str) -> bool:
        """
        Executes the query string

        Args:
            queryString (str): query string to execute

        Returns:
            bool: returns True if query is successful
        """
        if not super().exec(queryString):
            logger.error(f"query failed: {self.lastError().text()}")
            return False
        return True
        
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
            logger.error("selection failed: " + self.lastError().text())
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
            logger.error("selection failed: " + self.lastError().text())
            return False
        
    