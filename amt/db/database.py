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
        query = QSqlQuery(self)
        # allow foreign keys
        query.exec("PRAGMA foreign_keys = ON")

         
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
        
    