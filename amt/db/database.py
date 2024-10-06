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

import json, logging

from PySide6.QtSql import QSqlDatabase, QSqlQuery

class DatabaseError(Exception):
    def __init__(self, *args: object) -> None:
        """Class of database errors"""
        super().__init__(*args)

class DB:
    def __init__(self, databaseFile: str) -> None:
        """Class of database objects that provides an interface for SQLite queries.
        
        :param str databaseFile: path to the database file
        :raises DatabaseEroor: if the connection to the database can not be established
        """
        self.connection = QSqlDatabase.addDatabase("QSQLITE")
        self.connection.setDatabaseName(databaseFile)
        self.query = QSqlQuery()
        if not self.connection.open():
            raise DatabaseError(self.connection.lastError().text())
        self._createTables()

    def _createTables(self) -> None:
        """Create all necessary tables in the database."""
        self.query.exec(
            """
            CREATE TABLE IF NOT EXISTS author (
                author_id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                first_name VARCHAR,
                second_name VARCHAR,
                third_name VARCHAR,
                UNIQUE(first_name, second_name, third_name)
            )
            """
        )
        self.query.exec(
            """
            CREATE TABLE IF NOT EXISTS article (
                article_id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                title VARCHAR,
                arxiv_id VARCHAR,
                version INTEGER,
                date_published VARCHAR,
                date_updated VARCHAR,
                comment VARCHAR,
                link VARCHAR,
                link_pdf VARCHAR,
                p_category VARCAHR,
                doi VARCHAR,
                journal VARCHAR,
                summary VARCHAR,
                local_link VARCHAR,
                UNIQUE(title, version, date_published)
            )
            """
        )
        self.query.exec(
            """
            CREATE TABLE IF NOT EXISTS article_author (
                author_id INTEGER REFERENCES author,
                article_id INTEGER REFERENCES article
            )
            """
        )

        self.query.exec(
            """
            CREATE TABLE IF NOT EXISTS category (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                category VARCAHR UNIQUE
            )
            """
        )

        self.query.exec(
            """
            CREATE TABLE IF NOT EXISTS article_category (
                category_id INTEGER REFERENCES category,
                article_id INTEGER REFERENCES article
            )
            """
        )

    def select(self, table: str, columns : list = [], conds : dict = {}) -> bool:
        """selects from table columns according to conds
        
        :param list table: name of the table from which select data
        :param list columns: list of string containing column names to select, if list is empty * is assumed
        :param dist conds: dictionary of the form {col1 : [val1_1, val1_2, ...], col2 : [val2_1, val2_2, ...], ...} results in WHERE col1 IN (val1_1, val2_2, ...) AND col2 IN (val2_1, val2_2, ...) AND ...
        :return: True if the selection is sucessful
        :rtype: bool
        """
        queryString = "SELECT arg1 FROM arg2"
        if conds:
            queryString = queryString + " WHERE arg3"
        queryString = queryString.replace("arg2", table)
        if columns:
            queryString = queryString.replace("arg1", ", ".join(columns))
        else:
            queryString = queryString.replace("arg1", "*")
        if conds:
            condsString = ""
            for key in conds.keys():
                condsString += str(key) +" IN " + str(conds[key]).replace("[","(").replace("]",") AND ")
            condsString = condsString[0:-4]
            queryString = queryString.replace("arg3", condsString)
        if self.query.exec(queryString): 
            return True
        else: 
            logging.error("selection failed: " + self.query.lastError().text())
            return False

    def extract(self) -> list:
        """extracts data from db after query
        
        :returns: data from db
        :rtype: list
        """
        table = []
        row = []
        while self.query.next():
            row = []
            for i in range(self.query.record().count()):
                row.append(self.query.value(i))
            table.append(row)
        return table



    def insert(self, table: str, data: dict) -> bool:
        """inserts rows into a table
        
        :param str table: name of the table where insert rows to
        :param dist data: dictionary of the form {col1 : [val1_1, val1_2, ...], col2 : [val2_1, val2_2, ...], ...} results in WHERE col1 IN (val1_1, val2_2, ...) AND col2 IN (val2_1, val2_2, ...) AND ...
        :return: True if the insertion is sucessful
        :rtype: bool
        """
        dataValues = list(data.values())
        dataColumns = list(data.keys())
        #print(dataValues)
        if not DB._isRectangular(dataValues):
            logging.error("the data passed into insert is not consistent")
            return False
        queryString = "INSERT OR IGNORE INTO arg1 arg2 VALUES arg3"
        queryString = queryString.replace("arg1", table)
        queryString = queryString.replace("arg2", str(dataColumns).replace("[","(").replace("]",")") )
        arg3 = str(self._transpose(dataValues))[1:-1].replace("[","(").replace("]",")")
        queryString = queryString.replace("arg3", arg3)
        #print(queryString)
        if self.query.exec(queryString): 
            return True
        else: 
            logging.error("insertion failed: " + self.query.lastError().text())
            return False

    def delete(self, table: str, data: dict) -> bool:
        """removes row(s) from a table
        
        :param str table: table to modify
        :param dict data: dictionary that has column names as keys and values corresponding to the row(s) to remove
        :return: True if the removal is succesful
        :rtype: bool
        """
        queryString = "DELETE FROM arg1 WHERE arg2"
        queryString = queryString.replace("arg1", table)
        condsString = ""
        for key in data.keys():
            condsString += str(key) +" IN " + str(data[key]).replace("[","(").replace("]",") AND ")
        condsString = condsString[0:-4]
        queryString = queryString.replace("arg2", condsString)
        print(queryString)
        if self.query.exec(queryString): 
            return True
        else: 
            logging.error("deletion failed: " + self.query.lastError().text())
            return False
    


    @staticmethod
    def _transpose(l: list) -> list:
        """transopose a list of lists
        
        :param list l: list to be transposed
        :return: transposed list
        :rtype: list
        """
        if type(l[0]) == list:
            return list(map(list, zip(*l )))  
        else: 
            return [l]

    @staticmethod    
    def _isRectangular(n: list) -> bool:
        """check whether a list of list is rectangular
        
        :param list n: list of lists
        :return: True if the list of list rectangular
        :rtype: bool
        """
        if type(n[0]) == list: 
            return all(len(i) == len(n[0]) for i in n)
        else:
            return True

        
         