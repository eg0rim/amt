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

from PySide6.QtGui import QResizeEvent, QAction
from PySide6.QtWidgets import (
    QTableView,
    QMenu,
    QHeaderView,
    QWidget
)
from PySide6.QtCore import QAbstractItemModel, Qt
from PySide6.QtCore import QPoint

from amt.logger import getLogger

logger = getLogger(__name__)

class AMTTableWidget(QTableView):
    """
    A custom QTableView widget for the Article Management Tool (AMT) with additional features such as a context menu, 
    custom UI setup, and dynamic column resizing.
    Attributes:
        contextMenu (ATMTableContextMenu): The custom context menu for the table.
    Methods:
        __init__(self, parent=None)
        setupUI(self)
        showContextMenu(self, pos: QPoint)
        resizeEvent(self, event: QResizeEvent) -> None
        resizeColumns(self)
        getSelectedRows(self) -> list[int]
    """
    def __init__(self, parent: QWidget =None):
        """
        Initializes the ATMTable widget.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.

        Attributes:
            contextMenu (ATMTableContextMenu): The context menu for the table.
        """
        super().__init__(parent)
        # attributes
        # context menu
        self.contextMenu = AMTTableContextMenu(self)
        # setup ui 
        self.setupUI()
        
    def setupUI(self):
        """
        Sets up the user interface for the AMT table widget.
        """
        # set up the table
        # setup header
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        # no vertical header
        self.verticalHeader().setVisible(False)
        # select the whole row
        self.setSelectionBehavior(QTableView.SelectRows)
        # use custom context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        # allow sorting, model should support it
        self.setSortingEnabled(True)
        # seems to have strange behavior, sometimes it works, sometimes not?! figure out why
        self.setAlternatingRowColors(True) 
        # connect signal to show context menu
        self.customContextMenuRequested.connect(self.showContextMenu)   
        
    def showContextMenu(self, pos: QPoint):
        """
        Display the context menu at the specified position.

        Args:
            pos (QPoint): The position where the context menu should be displayed, relative to the widget.
        """
        # show context menu at the position of the mouse
        self.contextMenu.exec_(self.mapToGlobal(pos))
         
    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Handles the resize event for the widget.
        
        Args:
            event (QResizeEvent): The resize event object containing details
                                  about the resize event.
        """
        super().resizeEvent(event)
        # on resize change the width of the columns
        self.resizeColumns()
       
    def resizeColumns(self):
        """
        Resize the columns of the table to fit the table width.

        This method adjusts the width of each column in the table. The first column (title column) 
        is set to 50% of the total table width, while the remaining columns share the rest of the 
        width equally.

        Note:
            This method currently assumes a fixed fraction for the title column and equal distribution 
            for the remaining columns. It may need to be made more flexible for different use cases.
        """
        # resize columns to fit the table width
        tableWidth = self.width()
        # title column should be 50% of the table width
        defaultTitleFraction = 0.5
        numberOfColumns = self.model().columnCount()
        # rest of the columns should be equal
        for i in range(0, numberOfColumns-1):
            if i == 0:
                self.setColumnWidth(i, int(tableWidth * defaultTitleFraction))
            else:
                self.setColumnWidth(i, int(tableWidth * (1-defaultTitleFraction)/ float((numberOfColumns - 1))))
                
    def getSelectedRows(self) -> list[int]:
        """
        Get the selected rows in the table.
        
        Returns:
            list[int]: A list of row indices for the selected rows.
        """
        selectedIndexes = self.selectionModel().selectedRows()
        selectedRows = [index.row() for index in selectedIndexes]
        return selectedRows
    
class AMTMainTable(AMTTableWidget):
    """ 
    Specialized table widget for the main table in the Article Management Tool.
    """
    def __init__(self, parent: QWidget = None):
        """
        Initializes the AMTMainTable widget.
        
        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        # context menu
        self.contextMenu = AMTMainTableContextMenu(self)
        
class AMTArxivTable(AMTTableWidget):
    """ 
    Specialized table widget for the arXiv table in the Article Management Tool.
    """
    def __init__(self, parent: QWidget = None):
        """
        Initializes the AMTArxivTable widget.
        
        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        # context menu
        self.contextMenu = AMTArxivTableContextMenu(self)
        
class AMTTableContextMenu(QMenu):
    """
    Custom context menu for the table widget.
    """
    def __init__(self, parent=None):
        """
        Initializes the custom table widget.
        
        Attributes:
            openAction (QAction): Action to open an item.
            editAction (QAction): Action to edit an item.
            deleteAction (QAction): Action to delete an item.
        """
        super().__init__(parent)
        # actions as attributes
        # that are shared by all context menus
        # TODO: show details
        # self.showDetailsAction: QAction = self.addAction("Show Details")
        
        self.triggered.connect(self.menuAction)
        
class AMTMainTableContextMenu(AMTTableContextMenu):
    """
    Custom context menu for the main table widget.
    """
    def __init__(self, parent=None):
        """
        Initializes the custom main table widget.
        
        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        # add additional actions
        self.openAction: QAction = self.addAction("Open")
        self.editAction: QAction = self.addAction("Edit")
        self.deleteAction: QAction = self.addAction("Remove")
        self.manageFileAction: QAction = self.addAction("Manage File")
        
class AMTArxivTableContextMenu(AMTTableContextMenu):
    """
    Custom context menu for the arXiv table widget.
    """
    def __init__(self, parent=None):
        """
        Initializes the custom arXiv table widget.
        
        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        # add additional actions
        self.openAction: QAction = self.addAction("Open arXiv page")
        self.openPDFAction: QAction = self.addAction("Open PDF")
        self.addToLibAction: QAction = self.addAction("Add to library")
        self.downloadAction: QAction = self.addAction("Add and download")
        
   