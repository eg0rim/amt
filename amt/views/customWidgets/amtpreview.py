# -*- coding: utf-8 -*-
# amt/views/customWidgets/amtpreview.py

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

"""display preview for entries"""

from PySide6.QtWidgets import QLabel, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from amt.file_utils.pdfpreview import PdfPreviewer
from amt.db.datamodel import EntryData
from amt.logger import getLogger

logger = getLogger(__name__)

class AMTPreviewLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScaledContents(False)
        self.setFixedSize(300,400)
        self.setFrameShape(QLabel.Box)
        self.setFrameShadow(QLabel.Sunken)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: white;")
        self.setText("No preview")
        self.pdfPreviewer: PdfPreviewer = PdfPreviewer(size=(self.width(), self.height()))
        self.entry: EntryData = None
        self.dpr = QApplication.primaryScreen().devicePixelRatio()
        
    def setEntry(self, entry: EntryData ):
        if not entry.fileName:
            self.setText("No preview")
            return
        if not entry.fileName.lower().endswith('.pdf'):
            self.setText("Unsupported file format")
            return
        qPixmap = self.pdfPreviewer.getPreview(entry)  
        if not qPixmap:
            self.setText("Failed to generate preview")
            return
        self.setPixmap(qPixmap)
            
    def clear(self):
        self.setText("No preview")
        self.setPixmap(QPixmap())
        
    def setFixedSize(self, width, height):
        super().setFixedSize(width, height)
        self.pdfPreviewer.size = (width, height)
        
    