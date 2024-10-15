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
    QWidget
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
from amt.views.customWidgets.amtmessagebox import (
    AMTInfoMessageBox, 
    AMTWarnMessageBox, 
    AMTErrorMessageBox
)

logger = getLogger(__name__)

class AddDialog(QDialog):
    """
    AddDialog is a QDialog subclass that provides a dialog for adding or editing entries.
    
    Attributes:
        ui (addDialog_ui.Ui_Dialog): The UI of the dialog.
        forms (dict[str, AbstractForm]): A dictionary mapping entry types to their respective forms.
        currentForm (AbstractForm): The current form being displayed.
        data (EntryData): The data retrieved if the dialog is accepted.
    Methods:
        __init__(self, parent=None, entryToEdit: EntryData = None):
        setupUI(self):
        changeForm(self, text):
        accept(self):
    """
    def __init__(self, parent=None, entryToEdit: EntryData = None):
        """
        Initializes the AddDialog.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
            entryToEdit (EntryData, optional): The entry data to edit. If provided, the dialog will be in edit mode. Defaults to None.

        Attributes:
            ui (addDialog_ui.Ui_Dialog): The UI of the dialog.
            forms (dict[str, AbstractForm]): A dictionary mapping entry types to their respective forms.
            data (EntryData): The data retrieved if the dialog is accepted.
        """
        super().__init__(parent=parent)
        # attributes
        # ui of the dialog
        self.ui: addDialog_ui.Ui_Dialog = addDialog_ui.Ui_Dialog()
        # available forms for different types of entries
        # list of forms in one-to-one correspondence to options of self.ui.entryTypeComboBox
        self.forms: dict[str, AbstractForm] = {"Article":ArticleForm(self), "Book": BookForm(self), "Lecture notes": LecturesForm(self)}
        # current form to display
        self.currentForm: AbstractForm = None
        # data retrieved if dialog is accepted
        self.data: EntryData = None
        # setup UI
        self.setupUI()      
        # if entry specified => edit mode
        if entryToEdit:
            # impossible to change type of entry as for different types different database tables are used
            self.ui.entryTypeComboBox.setVisible(False)
            if isinstance(entryToEdit, ArticleData):
                self.ui.entryTypeComboBox.setCurrentText("Article")
            elif isinstance(entryToEdit, BookData):
                self.ui.entryTypeComboBox.setCurrentText("Book")
            elif isinstance(entryToEdit, LecturesData):
                self.ui.entryTypeComboBox.setCurrentText("Lecture notes")
            else:
                raise ValueError("Unknown data type")
            self.currentForm.setData(entryToEdit)
        logger.info("AddDialog initialized")
        
    def setupUI(self):
        """Sets up the UI components for the dialog."""
        self.ui.setupUi(self)
        # fill in the combobox with available entry types
        self.ui.entryTypeComboBox.clear()
        self.ui.entryTypeComboBox.addItems(self.forms.keys())
        self.ui.entryTypeComboBox.setCurrentText("Article")
        # set current form according to the selected entry type
        self.currentForm: AbstractForm = self.forms[self.ui.entryTypeComboBox.currentText()]
        # hide all forms
        for form in self.forms.values():
            self.ui.formWidget.layout().addWidget(form)
            form.hide()
        # show current form
        self.currentForm.show()
        # change form when entry type is changed
        self.ui.entryTypeComboBox.currentTextChanged.connect(self.changeForm)
        # buttons behaviour
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        
    def changeForm(self, text):
        """
        Updates the current form based on the provided text.
        
        Args:
            text (str): The key to identify which form to display from the forms dictionary.
        """
        # emitted when entry type is changed
        # hide current form
        self.currentForm.hide()
        # update current form
        self.currentForm = self.forms[text]
        # show back
        self.currentForm.show()
        
    def accept(self):
        """
        Accept the data provided through the dialog and store it in the data attribute.        
        """
        self.data = self.currentForm.getData()
        logger.info(f"Data accepted: {self.data.toShortString()}")
        super().accept()
        
class AbstractForm(QWidget):
    """
    AbstractForm is a QWidget subclass that serves as a base class for forms in the application.
    Methods
    -------
    __init__(parent=None)
    getData() -> EntryData
    setData(data: EntryData)
    """

    def __init__(self, parent=None):
        """
        Initializes the AbstractForm instance.
        """
        super().__init__(parent=parent)
    
    def getData(self) -> EntryData:
        """
        Abstract method to retrieve data from the form.
        Must be implemented in subclasses.
        Returns:
            EntryData: retrieved data from the form.
        """
        pass
    
    def setData(self, data: EntryData):
        """
        Abstract method to set data into the form.
        Must be implemented in subclasses.
        Args:
            data (EntryData): data to fill in the form.
        """
        pass

class ArticleForm(AbstractForm):
    """
    A form for adding or editing an article entry.
    Implements AbstractForm.
    
    Methods:
        getMetadataFromArxiv()
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = articleForm_ui.Ui_Form()
        self.ui.setupUi(self)
        # connect get metadata button
        self.ui.getMetaButton.clicked.connect(self.getMetadataFromArxiv)
        
    def getData(self) -> ArticleData:
        ui = self.ui
        authorsStr = ui.authorLineEdit.text()
        authors = [AuthorData(name.strip()) for name in authorsStr.split(',')] if authorsStr else []
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
        """
        To be implemented in 0.2.0 version.
        Must retrieve metadata from arXiv based on the provided arXiv ID.
        """ 
        msgBox = AMTInfoMessageBox(self)
        msgBox.setText("This feature is not implemented yet.")
        msgBox.setInformativeText("It will be implemented in 0.2.0 version. Stay tuned!")
        msgBox.exec()
        
class BookForm(AbstractForm):
    """
    A form for adding or editing an book entry.
    Implements AbstractForm.
    """    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = bookForm_ui.Ui_Form()
        self.ui.setupUi(self)
        
    def getData(self) -> BookData:
        ui = self.ui
        authorsStr = ui.authorLineEdit.text()
        authors = [AuthorData(name.strip()) for name in authorsStr.split(',')] if authorsStr else []
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
    """
    A form for adding or editing an lecture notes entry.
    Implements AbstractForm.
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = lecturesForm_ui.Ui_Form()
        self.ui.setupUi(self)
        
    def getData(self) -> LecturesData:
        ui = self.ui
        authorsStr = ui.authorLineEdit.text()
        authors = [AuthorData(name.strip()) for name in authorsStr.split(',')] if authorsStr else []
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