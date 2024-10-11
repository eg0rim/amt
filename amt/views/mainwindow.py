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
#from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
    QDialog
)
from PySide6.QtGui import QIcon
from amt.db.model import AMTModel
from amt.db.database import AMTDatabaseError, AMTQuery
from amt.db.datamodel import ArticleData, AuthorData, BookData, LecturesData

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
            self.model = AMTModel("test.amtdb")
            logger.info(f"Model is connected")
        except AMTDatabaseError:
            logger.critical(f"Database Error: {self.model.db.lastError().text()}")
            QMessageBox.critical(
            None,
            "AMT",
            f"Database Error: {self.model.db.lastError().text()}",
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
        self.ui.actionNew_library.triggered.connect(self.newLibrary)
        self.ui.actionOpen_library.triggered.connect(self.openLibrary)
        self.ui.actionSave_library.triggered.connect(self.saveLibrary)
        self.ui.actionSave_as.triggered.connect(self.saveAsLibrary)
        # main table 
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.resizeColumnsToContents()
        # update table
        self.updateTable()
        
    def updateTable(self):
        logger.info(f"update table button clicked")
        self.model.update()
        
    def openAboutDialog(self):
        AboutDialog(self).exec()
        
    def openAddDialog(self):
        dialog = AddDialog(self)
        # if accepted add article to database and update table
        if dialog.exec() == QDialog.Accepted:
            #self.model.addArticle(dialog.data)
            logger.debug(f"add entry of type {type(dialog.data)}")
            self.updateTable()
    
    def deleteSelectedRows(self):
        logger.debug(f"delete selected rows")
    #     rows = [r.row() for r in self.ui.tableWidget.selectionModel().selectedRows()]
    #     if len(rows)<1:
    #         # QMessageBox.warning(
    #         #     self,
    #         #     "Warning!",
    #         #     f"No rows selected.",
    #         # )
    #         return False
    #     messageBox = QMessageBox.warning(
    #         self,
    #         "Warning!",
    #         f"Do you want to remove the selected articles ({len(rows)})?",
    #         QMessageBox.Ok | QMessageBox.Cancel,
    #     )
    #     if messageBox == QMessageBox.Ok:
    #         for row in rows:
    #             #self.model.deleteArticle(self.ui.tableWidget.item(row,0).text())
    #             logger.debug(f"delete row {row}")
    #         #self.updateTable()
    #         return True
    #     else:
    #         return False
            
    def debug(self):
        logger.debug("Debug button pressed")
        author = AuthorData("John James Jacob Doe")
        author.id = 4
        entry = BookData("Test 3", [author])
        entry.id = 3
        entry.edition = 5
        self.model.addEntry(entry)     
        
    def newLibrary(self):
        logger.debug("create new db library")
        
    def openLibrary(self):
        logger.debug("open db library")
        
    def saveLibrary(self):
        # NOTE: currently changes saved right away
        logger.debug("save db library")
        
    def saveAsLibrary(self):
        logger.debug("save as other file db library")
        