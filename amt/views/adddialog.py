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
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QDialogButtonBox,
    QMessageBox,
    QWidget,
    QLabel,
    QDateEdit,
    QDateTimeEdit
)
from PySide6.QtGui import *
import urllib.request

from amt.parser.parser import parseArxiv
import amt.views.build.addDialog_ui as addDialog_ui
import amt.views.build.articleForm_ui as articleForm_ui
import amt.views.build.bookForm_ui as bookForm_ui
import amt.views.build.lecturesForm_ui as lecturesForm_ui

from amt.logger import getLogger
from amt.db.datamodel import (
    ArticleData,
    BookData,
    LecturesData,
    AuthorData
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
        self.data = None
        
    def changeForm(self, text):
        self.currentForm.hide()
        self.currentForm = self.forms[text]
        self.currentForm.show()
          
    def accept(self):
        """Accept the data provided through the dialog."""
        self.data = self.currentForm.getData()
        super().accept()
        
class AbstractForm(QWidget):
    """abstract add form"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
    
    def getData(self):
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
        data.datePublished = ui.publishedDateEdit.date()
        data.dateArxivUploaded = ui.arXivUploadDateTimeEdit.dateTime()
        data.dateArxivUpdated = ui.arXivUploadDateTimeEdit.dateTime()
        return data
        
    def getMetadataFromArxiv(self):
        logger.debug("metadata requested")    
        # if not self.ui.arXivIDLineEdit.text():
        #     QMessageBox.critical(
        #         self,
        #         "Error!",
        #         f"You must provide arxiv id",
        #     )
        #     return
        # try:
        #     data = parseArxiv(self.ui.arXivIDLineEdit.text())
        # except urllib.error.URLError:
        #     QMessageBox.critical(
        #         self,
        #         "Error!",
        #         f"Check your internet connection",
        #     )
        #     return
        # if not data:
        #     QMessageBox.critical(
        #         self,
        #         "Error!",
        #         f"Article not found! Check the arXiv id",
        #     )
        #     return
        # self.ui.titleLineEdit.setText(data['title'])
        # self.ui.authorLineEdit.setText(', '.join(data['authors']))
        # self.ui.arXivIDLineEdit.setText(data['arxiv_id'])
        # self.ui.versionLineEdit.setText(data['version'])
        # self.ui.datePublishedLineEdit.setText(data['date_published'])
        # self.ui.dateUpdatedLineEdit.setText(data['date_updated'])
        # self.ui.linkLineEdit.setText(data['link'])
        
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
        data.datePublished = ui.datePublishedDateEdit.date()
        return data
        
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
        data.date = ui.dateDateEdit.date()
        return data
