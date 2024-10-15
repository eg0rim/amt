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
from amt.logger import getLogger

logger = getLogger(__name__)

class AMTDatabaseError(Exception):
    def __init__(self, *args: object) -> None:
        """Class of database errors"""
        super().__init__(*args)
        
class AMTDatabaseOpenError(AMTDatabaseError):
    def __init__(self, *args: object) -> None:
        """Class of database errors when the database can not be opened"""
        super().__init__(*args)

class AMTDatabase(QSqlDatabase):
    """
    AMTDatabase class that inherits from QSqlDatabase to manage an SQLite database for AMT.
    Methods:
        __init__(databaseFile: str, *args: object)
        __del__() -> None
        open() -> None
    """    
    def __init__(self, databaseFile : str, *args : object) -> None:
        """Inherits QSqlDatabase. Creates sqlite database for AMT.
        
        Args:
            databaseFile (str): path to the database file
        """
        super().__init__("QSQLITE", *args)
        self.setDatabaseName(databaseFile)

    def __del__(self):
        """ 
        Closes the database connection when the object is deleted.
        """
        if self.isOpen():
            self.close()
        logger.debug("database closed")

    def open(self):
        """ 
        Raises AMTDatabaseOpenError if the database can not be opened.
        Allows foreign keys by default.
        """
        if not super().open():
            errormsg=self.lastError().text()
            logger.critical(f"db open error: {errormsg}")
            raise AMTDatabaseOpenError(errormsg)
        query = QSqlQuery(self)
        # allow foreign keys
        query.exec("PRAGMA foreign_keys = ON")
        
        
class AMTQueryError(Exception):
    def __init__(self, *args: object) -> None:
        """Class of query errors"""
        super().__init__(*args)

class AMTUniqueConstraintError(AMTQueryError):
    def __init__(self, *args: object) -> None:
        """Class of unique constraint violation errors"""
        super().__init__(*args)
         
class AMTQuery(QSqlQuery):
    """
    AMTQuery class for constructing and executing SQL queries using QSqlQuery.
    Properties:
        queryString: str: current query string
        execStatus: bool: True if the query was recently executed successfully and query was not changed
    Methods:
        queryString() -> str:
            Returns the current query string.
        execStatus() -> bool:
            Returns the execution status of the last query.
        getState(state: str) -> bool:
            Returns the state of a specific query type.
        exec(query: str = None) -> bool:
            Executes the query string. Returns True if successful.
        createTable(table: str, columns: dict[str, str], ifNotExists: bool = True, addLines: list[str] = []) -> bool:
            Constructs a CREATE TABLE query. Returns True if successful.
        createTableAddLines(lines: list[str]) -> bool:
            Adds lines to the table creation query string. Returns True if successful.
        select(table: str, columns: list[str] = [], filter: str = "") -> bool:
            Constructs a SELECT query. Returns True if successful.
        selectByReference(table: str, refTable: str, id: str, refid: str, columns: list[str] = [], filter: str = "") -> bool:
            Constructs a SELECT query with JOIN. Returns True if successful.
        insert(table: str, values: dict[str, str], orIgnore: bool = False) -> bool:
            Constructs an INSERT query. Returns True if successful.
        delete(table: str, filter: str) -> bool:
            Constructs a DELETE query. Returns True if successful.
        update(table: str, values: dict[str, str], filter: str) -> bool:
            Constructs an UPDATE query. Returns True if successful.    
    """    
    def __init__(self, db : AMTDatabase):
        """ 
        Inherits QSqlQuery. Initializes the query object.
        Args:
            db (AMTDatabase): database object
        """
        super().__init__(db)
        self._db: AMTDatabase = db
        self._queryString: str = None
        self._states: dict[str, bool] = {
            "createTable": False,
            "select": False,
            "insert": False,
            "delete": False,
            "update": False
        }
        # TODO: perhaps add drop, alter
        self._execStatus: bool = False
    
    @property  
    def queryString(self) -> str:
        return self._queryString
    
    @property
    def execStatus(self) -> bool:
        return self._execStatus
                    
    def _resetStates(self) -> None:
        for key in self._states:
            self._states[key] = False
    
    def _setState(self, state : str, value : bool) -> None:
        self._resetStates()
        self._states[state] = value
        
    def getState(self, state : str) -> bool:
        return self._states[state]
        
    def exec(self, query: str = None) -> bool:
        """
        Executes the query string

        Args:
            queryString (str, optional): query string to execute; if None, uses the prepared query string. Defaults to None.

        Returns:
            bool: returns True if query is successful
        """
        if query:
            qs = query
        else:
            qs = self.queryString
        if not qs:
            logger.error("query is not prepared")
            return False
        logger.debug(f"Executing query: {qs}")
        if not super().exec(qs):
            logger.error(f"Query failed: {self.lastError().text()}")
            return False
        logger.debug(f"Query executed successfully")
        # after excution, reset query string and status
        self._queryString = None
        self._execStatus = True
        return True
        
    def createTable(self, table : str, columns : dict[str, str], ifNotExists : bool = True, addLines : list[str] = []) -> bool:
        """
        Constructs query:
            CREATE TABLE [IF NOT EXISTS] table (columns)

        Args:
            table (str): table to create
            columns (dict[str, str]): dictionary of column names and types
            ifNotExists (bool, optional): Defaults to True.
            addLines (list[str], optional): additional lines to add to the table creation query string. Defaults to [].
        Returns:
            bool: returns True if table creation query construction is successful
        """
        self._execStatus = False
        self._queryString = f"CREATE TABLE {"IF NOT EXISTS" if ifNotExists else ""} {table} ({", ".join([f"{col} {colType}" for col, colType in columns.items()])} {f", {", ".join(addLines)}" if addLines else ""})"
        self._setState("createTable", True)
        return True
    
    def createTableAddLines(self, lines : list[str]) -> bool:
        """
        Adds lines to the table creation query string

        Args:
            columns (list[str]): list of lines to add to the table creation query string

        Returns:
            bool: returns True if column addition query construction is successful
        """
        if not self.getState("createTable") or self._execStatus:
            logger.error("table creation query is not prepared")
            return False
        self._queryString = f"{self._queryString[:-1]}, {', '.join(lines)})"
        return True
        
    def select(self, table : str, columns : list[str] = [], filter : str = "") -> bool:
        """
        Constructs query:
            SELECT table.columns FROM table [WHERE filter]

        Args:
            table (str): table to select from
            columns (list[str], optional): list of columns to select. Defaults to []: select all
            filter (str, optional): Defaults to "".

        Returns:
            bool: True if selection query construction is successful
        """
        self._execStatus = False
        self._queryString = f"SELECT {", ".join(columns) if columns else "*"} FROM {table}"
        if filter:
            self._queryString += f" WHERE {filter}"
        self._setState("select", True)
        return True
    
    def selectByReference(self, table : str, refTable : str, id : str, refid : str, columns : list[str] = [], filter : str = "") -> bool:
        """
        Constructs query:
            SELECT table.columns FROM table JOIN refTable ON table.id = refTable.refid [WHERE filter]

        Args:
            table (str): table to select from
            refTable (str): reference table
            id (str): identifier column in table
            refid (str): corresponding reference column in ref table
            columns (list[str], optional): columns to select. Defaults to []: select all columns
            filter (str, optional): Defaults to "".

        Returns:
            bool: returns True if selection query construction is successful
        """
        self._execStatus = False
        self._queryString = f"SELECT {", ".join([f"{table}.{column}" for column in columns]) if columns else f"{table}.*"} FROM {table} JOIN {refTable} ON {table}.{id} = {refTable}.{refid}"
        if filter:
            self._queryString += f" WHERE {filter}"
        self._setState("select", True)
        return True
        
    def insert(self, table : str, values : dict[str, str], orIgnore: bool = False) -> bool:
        """
        Constructs query:
            INSERT INTO [OR IGNORE] table (columns) VALUES (values)
        Insertion values can be str or None. If None, NULL is inserted.
        Args:
            table (str): table to insert into
            values (dict[str, str]): dictionary of column names and values

        Returns:
            bool: returns True if insertion query construction is successful
        """
        self._execStatus = False
        self._queryString = f"INSERT{' OR IGNORE' if orIgnore else ''} INTO {table} ({', '.join(values.keys())}) VALUES ({', '.join([f"'{val}'" if not val is None else "NULL" for val in values.values()])})"
        self._setState("insert", True)
        return True
    
    def delete(self, table : str, filter : str) -> bool:
        """
        Constructs query:
            DELETE FROM table WHERE filter

        Args:
            table (str): table to delete from
            filter (str): filter for deletion

        Returns:
            bool: returns True if deletion query construction is successful
        """
        self._execStatus = False
        self._queryString = f"DELETE FROM {table} WHERE {filter}"
        self._setState("delete", True)
        return True
    
    def update(self, table : str, values : dict[str, str], filter : str) -> bool:
        """
        Constructs query:
            UPDATE table SET values WHERE filter

        Args:
            table (str): table to update
            values (dict[str, str]): dictionary of column names and values
            filter (str): filter for updating

        Returns:
            bool: returns True if update query construction is successful
        """
        self._execStatus = False
        self._queryString = f"UPDATE {table} SET {', '.join([f"{col} = {"NULL" if val is None else f"'{val}'"}" for col, val in values.items()])} WHERE {filter}"
        self._setState("update", True)
        return True