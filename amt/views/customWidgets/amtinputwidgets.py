# -*- coding: utf-8 -*-
# amt/views/customWidgets/amtinputwidgets.py

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

"""custom input widgets"""

from PySide6.QtWidgets import (
    QDateTimeEdit, 
    QWidget, 
    QCheckBox, 
    QHBoxLayout, 
    QLineEdit, 
    QPushButton, 
    QFileDialog,
    QComboBox,
    QLabel,
    QGridLayout
)
from PySide6.QtCore import Signal
import re

from amt.views.customWidgets.amtfiledialog import AMTChooseFileDialog, AMTChooseEntryFileDialog, AMTChooseAppFileDialog

class AMTDateTimeEdit(QDateTimeEdit):
    """
    Custom QDateTimeEdit widget for the Article Management Tool (AMT). Iherits from QDateTimeEdit.
    Has fixed display format "dd/MM/yyyy hh:mm:ss".
    dateTime, date and time methods return None if the widget is disabled.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDisplayFormat("dd/MM/yyyy hh:mm:ss")
        
    def dateTime(self):
        if not self.isEnabled():
            return None
        return super().dateTime()
    
    def date(self):
        if not self.isEnabled():
            return None
        return super().date()
    
    def time(self):
        if not self.isEnabled():
            return None
        return super().time()

class AMTDateEdit(QDateTimeEdit):
    """ 
    Custom QDateTimeEdit widget for the Article Management Tool (AMT). Inherits from QDateTimeEdit.
    Has fixed display format "dd/MM/yyyy".
    dateTime, date and time methods return None if the widget is disabled.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDisplayFormat("dd/MM/yyyy")
        
    def dateTime(self):
        if not self.isEnabled():
            return None
        return super().dateTime()
    
    def date(self):
        if not self.isEnabled():
            return None
        return super().date()
    
    def time(self):
        if not self.isEnabled():
            return None
        return super().time()
    
class AMTDateTimeInput(QWidget):
    """ 
    Composite widget for date and time input. Contains a checkbox to enable/disable the widget.
    checactiveCheckBoxhBox enables/disables the AMTDateTimeEdit widget.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dateTimeEdit = AMTDateTimeEdit(self)
        self.activeCheckBox = QCheckBox(self)
        self.setLayout(QHBoxLayout(self))
        self.layout().addWidget(self.activeCheckBox)
        self.layout().addWidget(self.dateTimeEdit)
        self.layout().setStretch(0, 0)
        self.layout().setStretch(1, 1)
        self.activeCheckBox.setChecked(False)
        self.dateTimeEdit.setEnabled(False)
        self.activeCheckBox.stateChanged.connect(self.dateTimeEdit.setEnabled)
        
    def getDateTime(self):
        return self.dateTimeEdit.dateTime()
    
    def setDateTime(self, dateTime):
        if not dateTime:
            self.activeCheckBox.setChecked(False)
            return
        self.activeCheckBox.setChecked(True)
        self.dateTimeEdit.setDateTime(dateTime)

class AMTDateInput(QWidget):
    """ 
    Composite widget for date and time input. Contains a checkbox to enable/disable the widget.
    checactiveCheckBoxhBox enables/disables the AMTDateTimeEdit widget.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dateEdit = AMTDateEdit(self)
        self.activeCheckBox = QCheckBox(self)
        self.setLayout(QHBoxLayout(self))
        self.layout().addWidget(self.activeCheckBox)
        self.layout().addWidget(self.dateEdit)
        self.layout().setStretch(0, 0)
        self.layout().setStretch(1, 1)
        self.activeCheckBox.setChecked(False)
        self.dateEdit.setEnabled(False)
        self.activeCheckBox.stateChanged.connect(self.dateEdit.setEnabled)
        
    def getDate(self):
        return self.dateEdit.date()
    
    def setDate(self, date):
        if not date:
            self.activeCheckBox.setChecked(False)
            return
        self.activeCheckBox.setChecked(True)
        self.dateEdit.setDate(date)
        

class AMTFileIO(QWidget):
    """ 
    Composite widget for file input/output. Contains a QLineEdit and a QPushButton to browse for a file.
    If no file is selected, the filepath is an empty string. getFilePath returns None if no file is selected.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filepath = ""
        self.filepathEdit = QLineEdit()
        #self.filepathEdit.setReadOnly(True) # allow users to input file path manually
        self.filepathButton = QPushButton("Browse")
        self.filepathButton.clicked.connect(self.browseFile)
        self.fileDialog = AMTChooseFileDialog(self)
        self.setLayout(QHBoxLayout(self))
        self.layout().addWidget(self.filepathEdit)
        self.layout().addWidget(self.filepathButton)
        self.layout().setStretch(0, 1)
        self.layout().setStretch(1, 0)
        self.filepathEdit.textChanged.connect(self.onTextChanged)
    
    @property
    def filepath(self):
        return self._filepath
    
    @filepath.setter
    def filepath(self, filepath: str):
        self._filepath = filepath
        self.filepathEdit.setText(filepath)
        
    def browseFile(self):
        if self.filepath:
            self.fileDialog.selectFile(self.filepath)
        if self.fileDialog.exec() == QFileDialog.Accepted:
            self.filepath = self.fileDialog.selectedFile()
        
    def getFilePath(self) -> str | None:
        """ 
        Returns the filepath from the QLineEdit. Returns None if the filepath is an empty string.
        Returns:
            str | None: The filepath from the QLineEdit.
        """
        if self.filepath == "":
            return None
        return self.filepath
    
    def setFilePath(self, filepath: str | None):
        """ 
        Sets the filepath in the QLineEdit.
        Args:
            filepath (str): The filepath to set.
        """
        if filepath:
            self.filepath = filepath
        else:
            self.filepath = ""
    
    def onTextChanged(self, text: str):
        self._filepath = text
        
class AMTFileInput(AMTFileIO):
    """ 
    Specialization of AMTFileIO for file input.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fileDialog.setAcceptMode(QFileDialog.AcceptOpen)
        self.fileDialog.setFileMode(QFileDialog.ExistingFile)

class AMTFileOutput(AMTFileIO):
    """ 
    Specialization of AMTFileIO for file output.
    """
    def __init__(self, parent=None):
        super().__init__(parent)        
        self.fileDialog.setAcceptMode(QFileDialog.AcceptSave)
        self.fileDialog.setFileMode(QFileDialog.AnyFile)
        
class AMTBibtexFileOutput(AMTFileOutput):
    """ 
    Specialization of AMTFileOutput for bibtex file output.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fileDialog.setNameFilter("Bibtex Files (*.bib)")
        self.fileDialog.setDefaultSuffix("bib")

class AMTEntryFileInput(AMTFileInput):
    """ 
    Composite widget for entry file input. Contains a QLineEdit and a QPushButton to browse for a file.
    If no file is selected, the filepath is an empty string. getFilePath returns None if no file is selected.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fileDialog = AMTChooseEntryFileDialog(self)
        
class AMTAppFileInput(AMTFileInput):
    """ 
    Composite widget for executable file input. Contains a QLineEdit and a QPushButton to browse for a file.
    If no file is selected, the filepath is an empty string. getFilePath returns None if no file is selected.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fileDialog = AMTChooseAppFileDialog(self)        

class AMTLineEdit(QLineEdit):
    """ 
    Custom QLineEdit widget for the Article Management Tool (AMT). Inherits from QLineEdit.
    text method returns None if the lineEdit is empty.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def text(self):
        text =  super().text()
        if text == "":
            return None
        return text
    
class AMTSearchInput(QWidget):
    """ 
    Composite widget for search input. Contains a QComboBox to select the column to search in and a QLineEdit to input the search text.
    If input text starts with "/", the search is performed using regex.
    
    Emits: 
        searchInputChanged(int, str, bool): Signal emitted when the search input is changed. The signal contains the index of the selected column, the search text, and a boolean indicating if the search should be performed using regex.
    
    Attributes:
        columns (list[str]): List of columns to search in.
        searchLineEdit (AMTLineEdit): LineEdit widget for the search text.
        filterComboBox (QComboBox): ComboBox widget for selecting the column to search in.
    
    Methods:
        __init__(self, parent=None)
        setupUI(self)
        addColumns(self, columns: list[str])
        setColumns(self, columns: list[str])
        toggleVisible(self)
        text(self) -> tuple[str, bool]
        reset(self)
        onSearchLineEditChange(self, _)
        onFilterComboBoxChange(self, _)
    """
    searchInputChanged = Signal(int, str, bool)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.columns: list[str] = ["All"]
        self.searchLineEdit = AMTLineEdit(self)
        self.filterComboBox = QComboBox(self)
        self.errorLabel = QLabel(self)
        #self.regexCheckBox = QCheckBox("Use regex", self)
        self.setupUI()
    
    def setupUI(self):
        """
        Sets up the user interface for the custom widget.
        """
        self.searchLineEdit.setPlaceholderText("Start search string with '/' for using regex")
        layout = QGridLayout(self)
        self.setLayout(layout)
        layout.addWidget(self.filterComboBox, 0, 0)
        layout.addWidget(self.searchLineEdit, 0, 1)
        layout.addWidget(self.errorLabel, 1, 0, 1, 2)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        layout.addWidget(self.errorLabel)
        self.errorLabel.setVisible(False)
        self.errorLabel.setText("Invalid regex") 
        self.errorLabel.setStyleSheet("color: red;")       
        self.setVisible(False)
        self.filterComboBox.addItems(self.columns)
        # any changes in the searchLineEdit or filterComboBox should emit the searchInputChanged signal
        self.searchLineEdit.textChanged.connect(self.onSearchLineEditChange)
        self.filterComboBox.currentIndexChanged.connect(self.onFilterComboBoxChange)
        # hide on esc
        self.hideAction = self.addAction("Hide")
        self.hideAction.setShortcut("Esc")
        self.hideAction.triggered.connect(self.toggleVisible)
        
    def addColumns(self, columns: list[str]):
        """
        Adds a list of columns to the existing columns and updates the filterComboBox.
        Args:
            columns (list[str]): A list of column names to be added.
        """
        self.columns += columns
        self.filterComboBox.addItems(columns)
        
    def setColumns(self, columns: list[str]):
        """ 
        Resets the columns to the given list of columns and updates the filterComboBox.
        Args:
            columns (list[str]): A list of column names to be set.
        """
        self.columns = columns
        self.filterComboBox.clear()
        self.filterComboBox.addItems(columns)    
        
    def toggleVisible(self):
        """ 
        Toggle the visibility of the widget.
        """
        self.setVisible(not self.isVisible())
        
    def text(self) -> tuple[str, bool]:
        """ 
        Returns the text from the searchLineEdit and a boolean indicating if the text to be interpreted as a regex.
        Returns:
            tuple[str, bool]: The search text and a boolean indicating if the text is a regex.
        """
        text =self.searchLineEdit.text() or ""
        if text.startswith("/"):
            return text[1:], True
        return text, False
    
    def reset(self):
        """ 
        Resets the searchLineEdit and filterComboBox to their default values.
        """
        self.searchLineEdit.clear()
        self.filterComboBox.setCurrentIndex(0)
    
    def onSearchLineEditChange(self, _):
        """ 
        If the searchLineEdit text is changed, emit the searchInputChanged signal.
        """
        text, isRegex = self.text()
        index = self.filterComboBox.currentIndex()
        self.testSearchRegex()
        self.searchInputChanged.emit(index, text, isRegex)
        
    def onFilterComboBoxChange(self, _):
        """ 
        If the filterComboBox selection is changed, emit the searchInputChanged signal.
        """
        text, isRegex = self.text()
        index = self.filterComboBox.currentIndex()
        self.searchInputChanged.emit(index, text, isRegex)
        
    def testSearchRegex(self):
        """ 
        Test the search text for regex validity.
        """
        text, isRegex = self.text()
        if isRegex:
            try:
                re.compile(text)
                self.errorLabel.setVisible(False)
            except re.error:
                self.errorLabel.setVisible(True)
        else:
            self.errorLabel.setVisible(False)   