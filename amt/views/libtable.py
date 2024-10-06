# -*- coding: utf-8 -*-
# amt/views/libtable.py

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

"""library table widget"""

from PySide6.QtWidgets import (
    QTableWidget,
    QMenu,
    QMessageBox
)

class LibTableWidget(QTableWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.horizontalHeader().sortIndicatorChanged.connect(self.sortItems)

    def contextMenuEvent(self, event):    
        menu = QMenu(self)
        #quitAction = menu.addAction("Quit")
        #action = menu.exec_(self.mapToGlobal(event.pos()))
        #if action == quitAction:
        #    qApp.quit()
        editMetaAction = menu.addAction("Edit metadata")
        #action =  menu.exec_(self.mapToGlobal(event.pos()))
    
    def resizeColumns(self):
        tWidth = self.width()
        tColNum = self.columnCount()
        for i in range(1, tColNum-1):
            if i == 2:
                self.setColumnWidth(i, int(tWidth * 0.6))
            else:
                self.setColumnWidth(i, int(tWidth * 0.4 / float((tColNum - 2))))
        
    def deleteSelected(self):
        rows = [r.row() for r in self.selectionModel().selectedRows()]
        if len(rows)<1:
            return QMessageBox.Cancel, rows
        messageBox = QMessageBox.warning(
            self,
            "Warning!",
            f"Do you want to remove the selected articles ({len(rows)})?",
            QMessageBox.Ok | QMessageBox.Cancel,
        )
        return messageBox, rows
    