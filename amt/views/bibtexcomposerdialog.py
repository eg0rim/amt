# -*- coding: utf-8 -*-
# amt/views/bibtexcomposerdialog.py

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

"""dialog widget for composing bibtex file"""

from PySide6.QtCore import Qt, QItemSelection
from PySide6.QtWidgets import QDialog, QWidget, QAbstractItemView
import os

from amt.views.build.bibtexcomposerdialog_ui import Ui_BibtexComposerDialog
from amt.db.datamodel import EntryData 
from amt.db.tablemodel import BibtexComposerModel
from amt.views.customWidgets.amtmessagebox import AMTErrorMessageBox, AMTWarnMessageBox

from amt.logger import getLogger

logger = getLogger(__name__)

class BibtexComposerDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.model: BibtexComposerModel = BibtexComposerModel(self)
        self.setupUi()
        self.setupModel()
        self.currentEntry: EntryData | None = None
        
       
    def setupUi(self) -> None:
        self.ui = Ui_BibtexComposerDialog()
        self.ui.setupUi(self)
        # make the dialog window a normal window
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        # shortcuts
        self.addAction(self.ui.actionRemoveEntry)
        self.ui.actionRemoveEntry.triggered.connect(self.onRemoveTriggered)
        # compose button
        self.ui.composeButton.clicked.connect(self.composeBibtex)
        # allow only single selection
        self.ui.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        # no context menu
        self.ui.tableView.setContextMenuPolicy(Qt.NoContextMenu)
        
    def setupModel(self) -> None:
        self.ui.tableView.setModel(self.model)
        # when selection changes
        self.ui.tableView.selectionModel().selectionChanged.connect(self.onSelectionChanged)

        
    def addEntries(self, entries: list[EntryData]) -> None:
        self.model.addEntries(entries)
            
    def removeSelectedEntries(self) -> None:
        selectedRows = self.ui.tableView.getSelectedRows()
        self.model.removeEntriesAt(selectedRows)
        
    def onSelectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        # save the bibtex of the deselected row
        try: 
            row = deselected.indexes()[0].row()
            bibtex = self.ui.bibtexTextEdit.toPlainText()
            self.model.setBibtexAt(row, bibtex)
        except IndexError:
            pass
        # set the bibtex edit widget to the selected row
        try:
            row = selected.indexes()[0].row()
            bibtex = self.model.getBibtexAt(row)
            self.ui.bibtexTextEdit.setText(bibtex)
        except IndexError:
            pass
        
    def onRemoveTriggered(self) -> None:
        logger.debug("Remove action triggered")
        self.removeSelectedEntries()
        
    def composeBibtex(self) -> None:
        self.ui.tableView.clearSelection()
        logger.debug("Composing bibtex")
        #logger.debug(f"Composed bibtex:\n{self.model.composer.compose()}")
        filename = self.ui.bibtexFileInput.getFilePath()
        if not filename:
            msg = "No destination file specified."
            logger.error(msg)
            msgBox = AMTErrorMessageBox(self, msg)
            msgBox.exec()            
            return
        if os.path.exists(filename):
            msg = "File already exists. Overwrite?"
            logger.warning(msg)
            msgBox = AMTWarnMessageBox(self, msg)
            msgBox.setStandardButtons(AMTWarnMessageBox.Yes | AMTWarnMessageBox.No)
            if msgBox.exec() == AMTErrorMessageBox.No:
                return
        self.model.composer.write(filename)