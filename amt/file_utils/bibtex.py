# -*- coding: utf-8 -*-
# amt/file_utils/bibtex.py

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

"""class to compose and write bibtex file"""

from amt.db.datamodel import EntryData  

from amt.logger import getLogger

logger = getLogger(__name__)

class BibtexComposer:
    def __init__(self) -> None:
        self._entries: dict[EntryData, str] = {}
        
    def addEntry(self, entry: EntryData):
        if entry in self._entries:
            return
        bibtex = entry.bibtex
        self._entries[entry] = bibtex
        
    def removeEntry(self, entry: EntryData):
        try:
            del self._entries[entry]
        except KeyError:
            logger.error(f"Entry {entry} not found in composer")
            pass
        
    def setBibtex(self, entry: EntryData, bibtex: str) -> None:
        try:
            self._entries[entry] = bibtex
        except KeyError:
            logger.error(f"Entry {entry} not found in composer")
            pass
        
    def getBibtex(self, entry: EntryData) -> str:
        return self._entries[entry]

    def getEntries(self) -> dict[EntryData, str]:
        return self._entries.copy()
    
    def compose(self) -> str:
        bibtex = ""
        for b in self._entries.values():
            bibtex += b
            bibtex += "\n"
        return bibtex
    
    def write(self, file: str) -> None:            
        with open(file, "w") as f:
            f.write(self.compose())