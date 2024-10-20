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

from amt.logger import getLogger
from amt.db.datamodel import (
    ArticleData,
    BookData,
    LecturesData,
    AuthorData,
    EntryData,
    PublishableData
)
from amt.views.customWidgets.amtmessagebox import (
    AMTInfoMessageBox, 
    AMTWarnMessageBox, 
    AMTErrorMessageBox
)
from amt.views.customWidgets.entryforms import (
    ArticleForm,
    BookForm,
    LecturesForm,
    EntryForm
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
        # data retrieved if dialog is accepted
        self.data: EntryData = None
        # dict of forms and names
        self.forms = {
            "Article": ArticleForm(self),
            "Book": BookForm(self), 
            "Lecture notes": LecturesForm(self)
        }     
        # current widget
        self.currentForm: EntryForm = None
        # setup UI
        self.setupUI()      
        #if entry specified => edit mode
        if entryToEdit:
            # impossible to change type of entry as for different types different database tables are used
            self.ui.entryTypeComboBox.setVisible(False)
            self.setWindowTitle("Edit entry")
            if isinstance(entryToEdit, ArticleData):
                self.ui.entryTypeComboBox.setCurrentText("Article")
            elif isinstance(entryToEdit, BookData):
                self.ui.entryTypeComboBox.setCurrentText("Book")
            elif isinstance(entryToEdit, LecturesData):
                self.ui.entryTypeComboBox.setCurrentText("Lecture notes")
            else:
                raise ValueError("Unknown data type")
            self.ui.formStackedWidget.currentWidget().setData(entryToEdit)
        logger.info("AddDialog initialized")
        
    def setupUI(self):
        """Sets up the UI components for the dialog."""
        self.ui: addDialog_ui.Ui_Dialog = addDialog_ui.Ui_Dialog()
        self.ui.setupUi(self)
        defaultForm = "Article"
        # fill in the combobox with available entry types
        self.ui.entryTypeComboBox.addItems(self.forms.keys())
        self.ui.entryTypeComboBox.setCurrentText(defaultForm)
        # fill in stacked widget with forms
        for form in self.forms.values():
            self.ui.formStackedWidget.addWidget(form)
        self.ui.formStackedWidget.setCurrentWidget(self.forms[defaultForm])
        # set current form
        self.currentForm = self.forms[defaultForm]
        # change form when entry type is changed
        self.ui.entryTypeComboBox.currentTextChanged.connect(self.changeForm)
        self.ui.formStackedWidget.currentChanged.connect(self.setCurrentForm)
        # buttons behaviour
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        
    def changeForm(self, text: str):
        """
        Updates the current form based on the provided text.
        
        Args:
            text (str): The key to identify which form to display from the forms dictionary.
        """
        self.ui.formStackedWidget.setCurrentWidget(self.forms[text])
        
    def setCurrentForm(self, index: int):
        """
        Updates the current form based on the provided index.
        
        Args:
            index (int): The index of the form to display.
        """
        self.currentForm = self.ui.formStackedWidget.widget(index)
        
    def accept(self):
        """
        Accept the data provided through the dialog and store it in the data attribute.        
        """
        self.data = self.currentForm.getData()
        logger.info(f"Data accepted: {self.data.toShortString()}")
        super().accept()
        
