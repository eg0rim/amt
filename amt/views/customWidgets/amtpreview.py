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
        self.pdfPreviewer: PdfPreviewer = PdfPreviewer(size=(self.width(), self.height()))
        self.entry: EntryData = None
        self.setFixedSize(300,400)
        self.setScaledContents(False)
        self.setFrameShape(QLabel.Box)
        self.setFrameShadow(QLabel.Sunken)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: white;")
        self.clear()
        self.setVisible(False)
        
    def setEntry(self, entry: EntryData ):
        self.entry = entry
        # if not visible, do not generate preview
        if not self.isVisible():
            return
        # if entry is None, clear the preview
        if not entry:
            self.clear()
            return
        # if no file name, display "No preview"
        if not entry.fileName:
            self.setText("No preview")
            return
        # if file name is not among supported formats, display "Unsupported file format"
        if entry.fileName.lower().endswith('.pdf'):
            qPixmap = self.pdfPreviewer.getPreview(entry) 
        else:
            self.setText("Unsupported file format")
            return
        if not qPixmap:
            self.setText("Failed to generate preview")
            return
        self.setPixmap(qPixmap)
            
    def clear(self):
        self.setPixmap(QPixmap())
        self.setText("No preview")
        
    def reset(self):
        self.clear()
        self.pdfPreviewer.clearCache()
           
    def setFixedSize(self, width, height):
        super().setFixedSize(width, height)
        self.pdfPreviewer.size = (width, height)
        self.setEntry(self.entry)
        
    def toggleVisibility(self):
        self.setVisible(not self.isVisible())
        self.setEntry(self.entry)
        
    