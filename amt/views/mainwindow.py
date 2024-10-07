# -*- coding: utf-8 -*-
# amt/views/mainwindow.py

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

"""main window for the app"""

import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
    QDialog
)
from PySide6.QtGui import *
from amt.db.model import AmtModel
from amt.parser.parser import parseArxiv
from amt.db.database import DatabaseError

from  .build.resources_qrc import *
from .build.mainwindow_ui import (
    Ui_MainWindow
)

from .aboutdialog import AboutDialog
from .adddialog import AddDialog

from amt.logger import getLogger

logger = getLogger(__name__)

class MainWindow(QMainWindow):
    """main window"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # connect a model to the UI
        try:
            self.model = AmtModel()
            logger.info(f"Model is connected")
        except DatabaseError:
            logger.critical(f"Database Error: {self.model.db.connection.lastError().text()}")
            QMessageBox.critical(
            None,
            "AMT",
            f"Database Error: {self.model.db.connection.lastError().text()}",
            )
            sys.exit(1)
        # setup ui
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # add icons
        self.ui.actionAdd.setIcon(QIcon(":add.png"))
        self.ui.actionDel.setIcon(QIcon(":remove.png"))
        self.ui.actionUpdate.setIcon(QIcon(":update.png"))
        self.ui.actionDebug.setIcon(QIcon(":bug.png"))
        # actions in toolbar
        self.ui.actionAdd.triggered.connect(self.openAddDialog)
        self.ui.actionDebug.triggered.connect(self.debug)
        self.ui.actionDel.triggered.connect(self.deleteSelectedRows)
        self.ui.actionUpdate.triggered.connect(self.updateTable)
        # actions in menu
        self.ui.actionQuit.triggered.connect(self.close)
        self.ui.actionAbout.triggered.connect(self.openAboutDialog)
        
        
        # update table
        self.updateTable()
        
    def updateTable(self):
        data = self.model.extractArticles()
        numrows = len(data)
        if numrows < 1: 
            logger.info(msg="database is empty")
            return 
        numcols = 3
        self.ui.tableWidget.setRowCount(numrows)
        #print(numcols, numrows)
        #print(data)
        for row in range(numrows):
            for col in range(numcols):
                self.ui.tableWidget.setItem(row, col,QTableWidgetItem(str(data[row][col])))
        #self.resizeColumns()
        
    def openAboutDialog(self):
        AboutDialog(self).exec()
        
    def openAddDialog(self):
        dialog = AddDialog(self)
        # if accepted add article to database and update table
        if dialog.exec() == QDialog.Accepted:
            #self.model.addArticle(dialog.data)
            logger.debug(f"add entry of type {dialog.data["type"]} with data {dialog.data["data"]}")
            self.updateTable()
    
    def deleteSelectedRows(self):
        rows = [r.row() for r in self.ui.tableWidget.selectionModel().selectedRows()]
        if len(rows)<1:
            # QMessageBox.warning(
            #     self,
            #     "Warning!",
            #     f"No rows selected.",
            # )
            return False
        messageBox = QMessageBox.warning(
            self,
            "Warning!",
            f"Do you want to remove the selected articles ({len(rows)})?",
            QMessageBox.Ok | QMessageBox.Cancel,
        )
        if messageBox == QMessageBox.Ok:
            for row in rows:
                self.model.deleteArticle(self.ui.tableWidget.item(row,0).text())
            self.updateTable()
            return True
        else:
            return False
            
    def resizeEvent(self, event):
        """resize columns when window size is changed"""
        #self.ui.tableWidget.resizeColumns()
        return super(MainWindow, self).resizeEvent(event)
        
    def debug(self):
        logger.debug("Debug button pressed")
        