# -*- coding: utf-8 -*-
# amt/views/customWidgets/amtfiledialog.py

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

"""custom message boxes"""

from typing import List
from PySide6.QtWidgets import QFileDialog
from PySide6.QtGui import QIcon

from amt.views.build.resources_qrc import *

class AMTOpenDBFileDialog(QFileDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setNameFilter("AMT Database Files (*.amtdb)")
        self.setAcceptMode(QFileDialog.AcceptOpen)
        self.setWindowTitle("Open AMT Database")
        self.setFileMode(QFileDialog.ExistingFile)
        
    def selectedFile(self) -> str:
        return self.selectedFiles()[0]
    
class AMTSaveDBAsFileDialog(QFileDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setNameFilter("AMT Database Files (*.amtdb)")
        self.setAcceptMode(QFileDialog.AcceptSave)
        self.setWindowTitle("Save AMT Database")
        self.setFileMode(QFileDialog.AnyFile)
        
    def selectedFile(self) -> str:
        file =  self.selectedFiles()[0]   
        # force correct extension 
        if not file.endswith(".amtdb"):
            file += ".amtdb"
        return file
    
class AMTOpenEntryFileDialog(QFileDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setNameFilter("Entry Files (*.pdf *.djvu);;All Files (*)")
        self.setAcceptMode(QFileDialog.AcceptOpen)
        self.setWindowTitle("Open Entry File")
        self.setFileMode(QFileDialog.ExistingFile)
        
    def selectedFile(self) -> str:
        return self.selectedFiles()[0]