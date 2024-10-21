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

from PySide6.QtWidgets import QLabel, QApplication, QWidget, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from amt.file_utils.pdfpreview import PdfPreviewer
from amt.db.datamodel import EntryData
from amt.logger import getLogger

logger = getLogger(__name__)

class AMTPreviewLabel(QLabel):
    """ 
    Widget to display a preview of an entry.
    Properties:
        pdfPreviewer: PdfPreviewer object to generate the preview
    Methods:
        setEntry(entry: EntryData)
        clear()
        reset()
        setPreviewSize(width: int, height: int)
        toggleVisibility()
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pdfPreviewer: PdfPreviewer = PdfPreviewer(size=(self.width(), self.height()))
        self._entry: EntryData = None
        self.setScaledContents(False)
        self.setFrameShape(QLabel.Box)
        self.setFrameShadow(QLabel.Sunken)
        self.setAlignment(Qt.AlignCenter)
        self.clear()
        
    @property
    def pdfPreviewer(self) -> PdfPreviewer:
        return self._pdfPreviewer
        
    def setEntry(self, entry: EntryData ):
        """ 
        Display the preview of the entry.
        Args:
            entry: EntryData object to display the preview for
        """
        self._entry = entry
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
            qPixmap = self._pdfPreviewer.getPreview(entry) 
        else:
            self.setText("Unsupported file format")
            return
        if not qPixmap:
            self.setText("Failed to generate preview")
            return
        self.setPixmap(qPixmap)
            
    def clear(self):
        """ 
        Clear the preview.
        """
        self.setPixmap(QPixmap())
        self.setText("No preview")
        
    def reset(self):
        """
        Reset the preview to the initial state. And clear the cache.
        """
        self.clear()
        self._pdfPreviewer.clearCache()
           
    def setPreviewSize(self, width: int, height: int):
        """ 
        Set the size of the preview.
        Args:
            width: width of the preview in pixels
            height: height of the preview in pixels
        """
        self.setFixedHeight(height)
        self.setMinimumWidth(width)
        # update the size of the previewer
        self._pdfPreviewer.size = (width, height)
        self.setEntry(self._entry)
        
    def toggleVisibility(self):
        """ 
        Toggle the visibility of the preview widget.
        """
        self.setVisible(not self.isVisible())
        self.setEntry(self._entry)
        
class AMTPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        from amt.views.build.previewwidget_ui import Ui_previewWidget
        self.ui = Ui_previewWidget()
        self.ui.setupUi(self)
        self.setVisible(False)
        
    def setEntry(self, entry: EntryData):
        self.ui.previewLabel.setEntry(entry)
        self.ui.titleBody.setText(entry.getDisplayData('title'))
        self.ui.authorsBody.setText(entry.getDisplayData('authors'))
        self.ui.summaryBody.setText(entry.getDisplayData('summary'))
        
    def setPreviewSize(self, width: int, height: int):
        self.ui.previewLabel.setPreviewSize(width, height)
        
    def reset(self):
        self.ui.previewLabel.reset()
        self.ui.titleBody.clear()
        self.ui.authorsBody.clear()
        self.ui.summaryBody.clear()
        
    def toggleVisibility(self):
        self.setVisible(not self.isVisible())
        
    def clearCache(self):
        self.ui.previewLabel.pdfPreviewer.clearCache()