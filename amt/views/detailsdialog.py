# -*- coding: utf-8 -*-
# amt/views/detailsdialog.py

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

"""about dialog window"""

from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit
)
from .build.detailsDialog_ui import (
    Ui_DetailsDialog
)
from amt.db.datamodel import EntryData
from amt.logger import getLogger

logger = getLogger(__name__)

class DetailsDialog(QDialog):
    maxRowNum = 10
    maxCharNum = 50
    """
    Show details dialog window with the information about the entry.
    """
    def __init__(self, entry : EntryData, parent=None):
        super().__init__(parent)
        self.ui = Ui_DetailsDialog()
        self.ui.setupUi(self)
        self.setupEntryData(entry)
        
    def setupEntryData(self, entry : EntryData):
        """
        Setup entry data in the dialog.
        """
        data = entry.getDataToInsert()
        self.ui.typeLabel.setText(f"type: {type(entry).__name__}")
        layout = self.ui.detailsWidget.layout()
        column = 0
        rowCount = 0
        for key, value in data.items():
            if rowCount >= self.maxRowNum:
                column += 1
                rowCount = 0
            if not value:
                value = ""
            # truncate value
            # if len(value) > self.maxCharNum:
            #     value = value[:self.maxCharNum] + "..."
            keyLabel = QLabel(self)
            keyLabel.setText(key)
            valueField = QLineEdit(self)
            valueField.setText(value)
            valueField.setReadOnly(True)
            layout.addWidget(keyLabel, rowCount, 2* column)
            layout.addWidget(valueField, rowCount, 2* column + 1)
            rowCount += 1