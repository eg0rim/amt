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
    QDateTime
)

class AbstractData(object):
    def __init__(self):
        super().__init__()
    
    def toString(self):
        pass
    
    def toShortString(self):
        pass

class OrganizationData(AbstractData):
    """institute, university, company, etc data"""
    def __init__(self, orgName : str):
        super().__init__()
        self._name = orgName
        self._shortName = orgName
        self._address = None
        self._info = None
        
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
        return self.name
    
    def toShortString(self):
        return self.shortName

class AuthorData(AbstractData):
    """author data"""
    def __init__(self, name : str):
        # name is space separated string
        super().__init__()
        nameList = name.split(" ")
        self.firstName = nameList[0]
        if len(nameList) > 1:
            self.lastName = nameList[-1]
            self.middleNames = nameList[1:-1]
        else:
            self.lastName = ""
            self.middleNames = []
        self.affiliation = None
        self.bio = None
        self.birthDate = None
        self.deathDate = None
        
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
    
    def toString(self):
        return ' '.join([self.firstName] + self.middleNames + [self.lastName])
    
    def toShortString(self):
        return ' '.join([self.firstName] + [self.lastName])

class EntryData(AbstractData):
    """entry data"""
    def __init__(self, title : str, authors : list[AuthorData]):
        super().__init__()
        self._title = title
        self._authors = authors
        
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
        
class ArticleData(EntryData):
    """article data"""
    def __init__(self, title : str, authors : list[AuthorData]):
        super().__init__(title, authors)
        self._arxivid = None
        self._version = None
        self._journal = None
        self._doi = None
        self._link = None
        self._dateArxivUploaded = None
        self._dateArxivUpdated = None
        self._datePublished = None
        self._fileName = None

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

    @property
    def datePublished(self) -> QDate:
        return self._datePublished
    
    @datePublished.setter
    def datePublished(self, value : QDate):
        self._datePublished = value

    @property
    def fileName(self) -> str:
        return self._fileName
    
    @fileName.setter
    def fileName(self, value : str):
        self._fileName = value
        
class BookData(EntryData):
    """article data"""
    def __init__(self, title : str, authors : list[AuthorData]):
        super().__init__(title, authors)
        self._isbn = None
        self._publisher = None
        self._datePublished = None

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
    def datePublished(self) -> QDate:
        return self._datePublished

    @datePublished.setter
    def datePublished(self, value: QDate):
        self._datePublished = value
        
class LecturesData(EntryData):
    """article data"""
    def __init__(self, title : str, authors : list[AuthorData]):
        super().__init__(title, authors)
        self._school = None
        self._date = None
        self._course = None

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

    @property
    def date(self) -> QDate:
        return self._date

    @date.setter
    def date(self, value: QDate):
        self._date = value
        