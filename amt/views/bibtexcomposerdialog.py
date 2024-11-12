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

from amt.views.build.bibtexcomposerdialog_ui import Ui_BibtexComposerDialog
from amt.db.datamodel import EntryData 
from amt.db.tablemodel import BibtexComposerModel

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
        # actions
        # TODO: fix it
        self.ui.actionRemoveEntry.triggered.connect(self.removeSelectedEntries)
        # compose button
        self.ui.composeButton.clicked.connect(self.composeBibtex)
        
    def setupModel(self) -> None:
        self.ui.tableView.setModel(self.model)
        # when selection changes
        self.ui.tableView.selectionModel().selectionChanged.connect(self.onSelectionChanged)
        # allow only single selection
        self.ui.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        
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
            self.model.setBiBtexAt(row, bibtex)
        except IndexError:
            pass
        # set the bibtex edit widget to the selected row
        try:
            row = selected.indexes()[0].row()
            bibtex = self.model.getBibtexAt(row)
            self.ui.bibtexTextEdit.setText(bibtex)
        except IndexError:
            pass
        
        
        
    def onBibtexChanged(self, bibtex: str) -> None:
        self.model.bibtexCache
        
    def composeBibtex(self) -> None:
        logger.debug("Composing bibtex")
        # TODO: implement