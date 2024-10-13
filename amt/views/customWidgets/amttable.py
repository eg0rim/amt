# -*- coding: utf-8 -*-
# amt/views/customWidgets/amttable.py

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

from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import (
    QTableView,
    QMenu,
    QMessageBox,
    QHeaderView
)
from PySide6.QtCore import QAbstractItemModel, Qt, QModelIndex
from PySide6.QtCore import QPoint

from amt.db.tablemodel import AMTModel
from amt.logger import getLogger

logger = getLogger(__name__)

class AMTTableWidget(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        # set up the table
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setSortingEnabled(True)
        # define variables
        self.contextMenu = ATMTableContextMenu(self)
        self.customContextMenuRequested.connect(self.showContextMenu)   
        
    def showContextMenu(self, pos: QPoint):
        self.contextMenu.exec_(self.mapToGlobal(pos))
  
    def setModel(self, model: QAbstractItemModel | None) -> None:
        self.contextMenu.model = model
        super().setModel(model)
        
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        logger.debug(f"Table resized to {event.size()}")
        self.resizeColumns()
       
    def resizeColumns(self):
        # TODO: make it more flexible
        tableWidth = self.width()
        defaultTitleFraction = 0.5
        numberOfColumns = self.model().columnCount()
        for i in range(0, numberOfColumns-1):
            if i == 0:
                self.setColumnWidth(i, int(tableWidth * defaultTitleFraction))
            else:
                self.setColumnWidth(i, int(tableWidth * (1-defaultTitleFraction)/ float((numberOfColumns - 1))))
        
class ATMTableContextMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = None
        self.openAction = self.addAction("Open")
        self.editAction = self.addAction("Edit")
        self.deleteAction = self.addAction("Remove")
        self.triggered.connect(self.menuAction)
        
    @property
    def model(self):
        return self._model
    
    @model.setter
    def model(self, model : AMTModel):
        self._model = model
        
        
   