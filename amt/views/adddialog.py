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
    LecturesData
)

logger = getLogger(__name__)

class AddDialog(QDialog):
    """add dialog."""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = addDialog_ui.Ui_Dialog()
        self.ui.setupUi(self)
        # list of forms in one-to-one correspondence to options of self.ui.entryTypeComboBox
        self.forms = {"Article":ArticleForm(self), "Book": BookForm(self), "Lecture notes": LecturesForm(self)}
        self.ui.entryTypeComboBox.setCurrentText("Article")
        self.currentForm = self.forms[self.ui.entryTypeComboBox.currentText()]
        for form in self.forms.values():
            self.ui.formWidget.layout().addWidget(form)
            form.hide()
        self.currentForm.show()
        self.ui.entryTypeComboBox.currentTextChanged.connect(self.changeForm)
        # buttons behaviour
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        # data
        self.data = {"type": "Article", "data": None}
        
    def changeForm(self, text):
        self.currentForm.hide()
        self.currentForm = self.forms[text]
        self.currentForm.show()
        
    def getCurrentFormData(self):
        data = {}
        rcount = self.currentForm.ui.formLayout.rowCount()
        for i in range(rcount):
            label = self.currentForm.ui.formLayout.itemAt(i, QFormLayout.LabelRole).widget()
            field = self.currentForm.ui.formLayout.itemAt(i, QFormLayout.FieldRole).widget()
            # expect that label is always QLabel
            if not isinstance(label, QLabel):
                logger.error(f"unexpected label encountered: {label}; skipping")
                continue
            labelText = label.text()
            # expected fields: QLineEdit, QDateEdit, QDateTimeEdit
            data[labelText] = field
        return data
    
    def accept(self):
        """Accept the data provided through the dialog."""
        # self.data = {}
        # if not self.titleField.text():
        #     QMessageBox.critical(
        #         self,
        #         "Error!",
        #         f"You must provide article's title",
        #     )
        #     self.data = None  # Reset .data
        #     return
        # for field in (self.titleField,
        # self.authorsField,
        # self.arxivIdField,
        # self.versionField,
        # self.datePublishedField,
        # self.dateUpdatedField,
        # self.linkField):
        #     self.data[field.objectName()] = field.text()

        # if not self.data:
        #     return
        logger.debug(f"current fields: {self.getCurrentFormData()}")
        logger.debug("add accepted")
        self.data["type"] = self.ui.entryTypeComboBox.currentText()
        super().accept()
        
class AbstractForm(QWidget):
    """abstract add form"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
    
    @abstract
    def getData(self):
        pass

class ArticleForm(AbstractForm):
    """add article form"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = articleForm_ui.Ui_Form()
        self.ui.setupUi(self)
        self.ui.getMetaButton.clicked.connect(self.getMetadataFromArxiv)
        
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
        
class LecturesForm(AbstractForm):
    """add article form"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = lecturesForm_ui.Ui_Form()
        self.ui.setupUi(self)
