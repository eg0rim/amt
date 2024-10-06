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

import logging
from PySide6.QtCore import Qt
from PySide6.QtSql import QSqlTableModel, QSqlQuery
from .database import DB, DatabaseError
import sys

class AmtModel:

    def __init__(self):
        """Provides interface between database and view"""
        self.db = DB("db.sqlite")
    
    def extractArticles(self) -> list:
        """Extracts table of articles from the database
        
        :returns: table with article titles, authors, etc
        "rtype: list
        """
        table = []
        self.db.select("article", ["article_id", "title"])
        articleTable = self.db.extract()
        #print(articleTable)
        for articleEntry in articleTable:
            self.db.select("article_author", ["author_id"], {"article_id": [articleEntry[0]]})
            authorIds = self.db.extract()
            row = [articleEntry[0]]
            authors = []
            for authorId in authorIds:
                self.db.select("author", ["first_name", "second_name", "third_name"], {"author_id" : [authorId[0]]})
                author = self.db.extract()[0]
                author_name = " ".join(author)
                authors.append(author_name)
            row.append(', '.join(authors))
            row.append(articleEntry[1])
            #print(row)
            table.append(row)
        return(table)

    def addArticle(self, data):

        self.db.insert("article", {k: [data[k]] for k in ("title", "arxiv_id", "version", "date_published", "date_updated", "link")})
        self.db.select("article", ["article_id"], {"title": [data["title"]]})
        #print(self.db.extract())
        articleId = self.db.extract()[0][0]
        authors = data["authors"]         
        authorIds = []
        for author in authors.split(", "):
            #print(author)
            authorSplited = author.split(" ")
            #print(authorSplited)
            if len(authorSplited) == 2:
                self.db.insert("author", {"first_name": [authorSplited[0]], "second_name": [authorSplited[1]]})
                self.db.select("author", ["author_id"],{"first_name": [authorSplited[0]], "second_name": [authorSplited[1]]})
            elif len(authorSplited) == 3:
                self.db.insert("author", {"first_name": [authorSplited[0]], "second_name": [authorSplited[1]], "third_name": [authorSplited[2]]})
                self.db.select("author", ["author_id"],{"first_name": [authorSplited[0]], "second_name": [authorSplited[1]], "third_name": [authorSplited[2]]})
            else:
                return False
            
            authorIds.append(self.db.extract()[0][0])
            #print(query.lastInsertId())
        #print(authorIds)
        for authorId in authorIds:
            self.db.insert("article_author", {"article_id": articleId, "author_id": authorId})
        return True
        

    def deleteArticle(self, articleId):
        """Remove an entry from the database."""
        if not self.db.delete("article", {"article_id": [articleId]}):
            logging.error(msg="oops")
        #todo get rid of useless authors
        return True

