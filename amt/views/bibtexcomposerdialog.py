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

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QWidget

from amt.views.build.bibtexcomposerdialog_ui import Ui_BibtexComposerDialog
from amt.db.tablemodel import BibtexComposerModel

class BibtexComposerDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.model = BibtexComposerModel(self)
        self.setupUi()
        self.setupModel()
       
    def setupUi(self) -> None:
        self.ui = Ui_BibtexComposerDialog()
        self.ui.setupUi(self)
        # make the dialog window a normal window
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        
    def setupModel(self) -> None:
        self.ui.tableView.setModel(self.model)
        
    def addEntries(self, entries: list[dict[str, str]]) -> None:
        self.model.addEntries(entries)