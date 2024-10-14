# -*- coding: utf-8 -*-
# amt/views/adddialog.py

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

"""add dialog window"""

from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QMessageBox
)
from PySide6.QtGui import *

import amt.views.build.addDialog_ui as addDialog_ui
import amt.views.build.articleForm_ui as articleForm_ui
import amt.views.build.bookForm_ui as bookForm_ui
import amt.views.build.lecturesForm_ui as lecturesForm_ui

from amt.logger import getLogger
from amt.db.datamodel import (
    ArticleData,
    BookData,
    LecturesData,
    AuthorData,
    EntryData
)

logger = getLogger(__name__)

class AddDialog(QDialog):
    """add dialog."""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = addDialog_ui.Ui_Dialog()
        self.ui.setupUi(self)
        # list of forms in one-to-one correspondence to options of self.ui.entryTypeComboBox
        self.forms: dict[str, AbstractForm] = {"Article":ArticleForm(self), "Book": BookForm(self), "Lecture notes": LecturesForm(self)}
        self.ui.entryTypeComboBox.setCurrentText("Article")
        self.currentForm: AbstractForm = self.forms[self.ui.entryTypeComboBox.currentText()]
        for form in self.forms.values():
            self.ui.formWidget.layout().addWidget(form)
            form.hide()
        self.currentForm.show()
        self.ui.entryTypeComboBox.currentTextChanged.connect(self.changeForm)
        # buttons behaviour
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        # data
        self.data: EntryData = None
        
    def changeForm(self, text):
        self.currentForm.hide()
        self.currentForm = self.forms[text]
        self.currentForm.show()
          
    def accept(self):
        """Accept the data provided through the dialog."""
        self.data = self.currentForm.getData()
        super().accept()
           
    def setData(self, data: EntryData):
        self.ui.entryTypeComboBox.setVisible(False)
        if isinstance(data, ArticleData):
            self.ui.entryTypeComboBox.setCurrentText("Article")
        elif isinstance(data, BookData):
            self.ui.entryTypeComboBox.setCurrentText("Book")
        elif isinstance(data, LecturesData):
            self.ui.entryTypeComboBox.setCurrentText("Lecture notes")
        else:
            raise ValueError("Unknown data type")
        self.currentForm.setData(data)
        
class AbstractForm(QWidget):
    """abstract add form"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
    
    def getData(self) -> EntryData:
        pass
    
    def setData(self, data: EntryData):
        pass

class ArticleForm(AbstractForm):
    """add article form"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = articleForm_ui.Ui_Form()
        self.ui.setupUi(self)
        self.ui.getMetaButton.clicked.connect(self.getMetadataFromArxiv)
        
    def getData(self) -> ArticleData:
        ui = self.ui
        authorsStr = ui.authorLineEdit.text()
        authors = [AuthorData(name.strip()) for name in authorsStr.split(',')]
        title = ui.titleLineEdit.text()     
        data = ArticleData(title, authors)
        data.arxivid = ui.arXivIDLineEdit.text()
        data.version = ui.versionLineEdit.text()
        data.journal = ui.journalLineEdit.text()
        data.doi = ui.dOILineEdit.text()
        data.link = ui.linkLineEdit.text()
        data.datePublished = ui.publishedDateInput.dateEdit.date()
        data.dateArxivUploaded = ui.arxivUploadDatetimeInput.dateTimeEdit.dateTime()
        data.dateArxivUpdated = ui.arxivUpdateDateTimeInput.dateTimeEdit.dateTime()
        data.fileName = ui.fileInput.getFilePath()
        return data

    def setData(self, data: ArticleData):
        ui = self.ui
        ui.titleLineEdit.setText(data.title)
        ui.authorLineEdit.setText(', '.join([author.toString() for author in data.authors]))
        ui.arXivIDLineEdit.setText(data.arxivid)
        ui.versionLineEdit.setText(data.version)
        ui.journalLineEdit.setText(data.journal)
        ui.dOILineEdit.setText(data.doi)
        ui.linkLineEdit.setText(data.link)
        ui.publishedDateInput.setDate(data.datePublished)
        ui.arxivUploadDatetimeInput.setDateTime(data.dateArxivUploaded)
        ui.arxivUpdateDateTimeInput.setDateTime(data.dateArxivUpdated)
        ui.fileInput.filepath = data.fileName
        
    def getMetadataFromArxiv(self):
        logger.debug("metadata requested")   
        QMessageBox.information(
            self,
            "Information",
            "This feature will be implemented in 0.2.0 version. Stay tuned!",
        )
        
class BookForm(AbstractForm):
    """add article form"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = bookForm_ui.Ui_Form()
        self.ui.setupUi(self)
        
    def getData(self) -> BookData:
        ui = self.ui
        authorsStr = ui.authorLineEdit.text()
        authors = [AuthorData(name.strip()) for name in authorsStr.split(',')]
        title = ui.titleLineEdit.text()     
        data = BookData(title, authors)
        data.isbn = ui.iSBNLineEdit.text()
        data.publisher = ui.publisherLineEdit.text()
        data.datePublished = ui.publishedDateInput.dateEdit.date()
        data.fileName = ui.fileInput.getFilePath()
        return data
    
    def setData(self, data: BookData):
        ui = self.ui
        ui.titleLineEdit.setText(data.title)
        ui.authorLineEdit.setText(', '.join([author.toString() for author in data.authors]))
        ui.iSBNLineEdit.setText(data.isbn)
        ui.publisherLineEdit.setText(data.publisher)
        ui.publishedDateInput.setDate(data.datePublished)
        ui.fileInput.filepath = data.fileName
        
class LecturesForm(AbstractForm):
    """add article form"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = lecturesForm_ui.Ui_Form()
        self.ui.setupUi(self)
        
    def getData(self) -> LecturesData:
        ui = self.ui
        authorsStr = ui.authorLineEdit.text()
        authors = [AuthorData(name.strip()) for name in authorsStr.split(',')]
        title = ui.titleLineEdit.text()     
        data = LecturesData(title, authors)
        data.course = ui.courseLineEdit.text()
        data.school = ui.uniLineEdit.text()
        data.datePublished = ui.dateInput.dateEdit.date()
        data.fileName = ui.fileInput.getFilePath()
        return data

    def setData(self, data: LecturesData):
        ui = self.ui
        ui.titleLineEdit.setText(data.title)
        ui.authorLineEdit.setText(', '.join([author.toString() for author in data.authors]))
        ui.courseLineEdit.setText(data.course)
        ui.uniLineEdit.setText(data.school)
        ui.dateInput.setDate(data.datePublished)
        ui.fileInput.filepath = data.fileName