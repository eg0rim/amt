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

# TODO: promote it to inherit QAbstractTableModel
class AMTModel(QAbstractTableModel):
    def __init__(self, dbfile : str, *args : object):
        """Provides model to interact with db"""
        super().__init__(*args)
        self.db = AMTDatabase(dbfile)
        self.db.open()       
        self._columnCount= 2
        self._data : list[EntryData] = []
        
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
            int: _description_
        """
        return len(self._data)
    
    def data(self, index : QModelIndex, role : int = Qt.DisplayRole):
        if role == Qt.DisplayRole:
            entry = self._data[index.row()]
            return entry.getColumn(index.column())
        return None
                                   
    def extractEntries(self) -> list[EntryData]:
        """
        Returns all entries from article, book and lecture tables

        Returns:
            list[EntryData]: list of EntryData objects
        """
        entries = []
        query = AMTQuery(self.db)
        for table in ("article", "book", "lectures"):
            query.select(table)
            while query.next():
                entry = query.amtData(table)
                # return only valid entries
                if entry:
                    entries.append(entry)
                else:
                    logger.warning(f"invalid entry encountered in table {table} row {query.value(0)}")
        return entries
    
    # TODO: fix below            
    # def addArticle(self, data):

    #     self.db.insert("article", {k: [data[k]] for k in ("title", "arxiv_id", "version", "date_published", "date_updated", "link")})
    #     self.db.select("article", ["article_id"], {"title": [data["title"]]})
    #     #print(self.db.extract())
    #     articleId = self.db.extract()[0][0]
    #     authors = data["authors"]         
    #     authorIds = []
    #     for author in authors.split(", "):
    #         #print(author)
    #         authorSplited = author.split(" ")
    #         #print(authorSplited)
    #         if len(authorSplited) == 2:
    #             self.db.insert("author", {"first_name": [authorSplited[0]], "second_name": [authorSplited[1]]})
    #             self.db.select("author", ["author_id"],{"first_name": [authorSplited[0]], "second_name": [authorSplited[1]]})
    #         elif len(authorSplited) == 3:
    #             self.db.insert("author", {"first_name": [authorSplited[0]], "second_name": [authorSplited[1]], "third_name": [authorSplited[2]]})
    #             self.db.select("author", ["author_id"],{"first_name": [authorSplited[0]], "second_name": [authorSplited[1]], "third_name": [authorSplited[2]]})
    #         else:
    #             return False
            
    #         authorIds.append(self.db.extract()[0][0])
    #         #print(query.lastInsertId())
    #     #print(authorIds)
    #     for authorId in authorIds:
    #         self.db.insert("article_author", {"article_id": articleId, "author_id": authorId})
    #     return True
        

    # def deleteArticle(self, articleId):
    #     """Remove an entry from the database."""
    #     if not self.db.delete("article", {"article_id": [articleId]}):
    #         logging.error(msg="oops")
    #     #todo get rid of useless authors
    #     return True

