# -*- coding: utf-8 -*-
# amt/views/customWidgets/filemanager.py

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

"""widget to mange entry file"""

from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PySide6.QtWidgets import QMessageBox

from amt.file_utils.filehandler import EntryHandler
from amt.logger import getLogger
from amt.views.customWidgets.amtmessagebox import AMTWarnMessageBox
from amt.views.customWidgets.amtfiledialog import AMTChooseFileDialog, AMTChooseEntryFileDialog
from amt.db.datamodel import EntryData
from amt.db.tablemodel import AMTModel

logger = getLogger(__name__)

class FileManagerWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.fileLineEdit = QLineEdit(self)
        self.changeButton = QPushButton("Change", self)
        self.moveButton = QPushButton("Move", self)
        self.deleteButton = QPushButton("Delete", self)
        self.setupUi()
        self._entry: EntryData | None = None
        self._model: AMTModel  = None
        
    def setModel(self, model: AMTModel) -> None:
        """
        Set the model to manage.
        
        Parameters:
            model (AMTModel): the model to manage
        """
        self._model = model
        
    def setupUi(self) -> None:
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("current:"))
        self.fileLineEdit.setReadOnly(True)
        self.fileLineEdit.setPlaceholderText("no current file")
        layout.addWidget(self.fileLineEdit)
        layout.addWidget(self.changeButton)
        layout.addWidget(self.moveButton)
        layout.addWidget(self.deleteButton)
        self.setVisible(False)
        self.reset()
        # connect buttons
        self.deleteButton.clicked.connect(self.onDeleteButtonClicked)
        self.moveButton.clicked.connect(self.onMoveButtonClicked)
        self.changeButton.clicked.connect(self.onChangeButtonClicked)
    
    def reset(self) -> None:
        self.changeButton.setEnabled(False)
        self.deleteButton.setEnabled(False)
        self.moveButton.setEnabled(False)
        self._entry = None
        self.fileLineEdit.clear()
            
    def toggleVisible(self):
        """ 
        Toggle the visibility of the widget.
        """
        self.setVisible(not self.isVisible())
        
    def setEntry(self, entry: EntryData) -> None:
        """
        Set the entry to manage.
        
        Parameters:
            entry (EntryData): the entry to manage
        """
        self._entry = entry
        if entry.fileName:
            self.fileLineEdit.setText(entry.fileName)
            self.changeButton.setText("Change")
            self.changeButton.setEnabled(True)
            self.deleteButton.setEnabled(True)
            self.moveButton.setEnabled(True)
        else:
            self.fileLineEdit.clear()
            self.changeButton.setText("Add file")
            self.changeButton.setEnabled(True)
            self.deleteButton.setEnabled(False)
            self.moveButton.setEnabled(False)            
            
    def onDeleteButtonClicked(self) -> None:
        """
        Slot for delete button clicked signal.
        """
        warningMsg = "Are you sure you want to delete the file?"
        minorMsg = "This action cannot be undone.\nIf the file is referenced by another entry, the deletion will not be reflected there."
        msgBox = AMTWarnMessageBox(self)
        msgBox.setText(warningMsg)
        msgBox.setInformativeText(minorMsg)
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        if msgBox.exec() == QMessageBox.Yes:
            EntryHandler.deleteEntryFile(self._entry)
            if self._model:
                self._model.editEntryInPlace(self._entry)
            self.setEntry(self._entry)
            
    def onMoveButtonClicked(self) -> None:
        """
        Slot for move button clicked signal.
        """
        warningMsg = "Are you sure you want to move the file?"
        minorMsg = "This action cannot be undone.\nIf the file is referenced by another entry, the move will not be reflected there."
        msgBox = AMTWarnMessageBox(self)
        msgBox.setText(warningMsg)
        msgBox.setInformativeText(minorMsg)
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        if msgBox.exec() == QMessageBox.Yes:
            fileDialog = AMTChooseFileDialog(self)
            fileDialog.setAcceptMode(QFileDialog.AcceptSave)
            fileDialog.setFileMode(QFileDialog.AnyFile)
            fileDialog.selectFile(self._entry.fileName)
            if fileDialog.exec() == QFileDialog.Accepted:
                filePath = fileDialog.selectedFile()
                EntryHandler.renameEntryFile(self._entry, filePath)
                if self._model:
                    self._model.editEntryInPlace(self._entry)
                self.setEntry(self._entry)
                
    def onChangeButtonClicked(self) -> None:
        """
        Slot for change button clicked signal.
        """
        fileDialog = AMTChooseEntryFileDialog(self)
        if fileDialog.exec() == QFileDialog.Accepted:
            filePath = fileDialog.selectedFile()
            #newEntry = copy.deepcopy(self._entry)
            #newEntry.fileName = filePath
            self._entry.fileName = filePath
            if self._model:
                self._model.editEntryInPlace(self._entry)
            self.setEntry(self._entry)