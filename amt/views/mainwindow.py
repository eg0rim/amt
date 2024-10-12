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
    QDialog,
    QFileDialog
)
from PySide6.QtGui import QIcon
from amt.db.tablemodel import AMTModel
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
        # setup ui
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # create empty model (by default in a temp location)
        try:
            self.model = AMTModel()
            logger.info(f"Model is connected")
        except AMTDatabaseError:
            logger.critical(f"Database Error: {self.model.db.lastError().text()}")
            QMessageBox.critical(
            None,
            "AMT",
            f"Database Error: {self.model.db.lastError().text()}",
            )
            sys.exit(1)
        self.model.temporaryStatusChanged.connect(self.setTemporary)
        self.model.editedStatusChanged.connect(self.setEdited)
        self.model.update()
        self.setTemporary(True)
        self.setEdited(False)
        # add icons
        self.ui.actionAdd.setIcon(QIcon(":add.png"))
        self.ui.actionDel.setIcon(QIcon(":remove.png"))
        self.ui.actionUpdate.setIcon(QIcon(":update.png"))
        self.ui.actionDebug.setIcon(QIcon(":bug.png"))
        # actions in toolbar
        self.ui.actionAdd.triggered.connect(self.openAddDialog)
        self.ui.actionDebug.triggered.connect(self.debug)
        self.ui.actionDel.triggered.connect(self.deleteSelectedRows)
        self.ui.actionUpdate.triggered.connect(self.model.update)
        # actions in menu
        self.ui.actionQuit.triggered.connect(self.close)
        self.ui.actionAbout.triggered.connect(self.openAboutDialog)
        self.ui.actionNew_library.triggered.connect(self.newLibrary)
        self.ui.actionOpen_library.triggered.connect(self.openLibrary)
        self.ui.actionSave_library.triggered.connect(self.saveLibrary)
        self.ui.actionSave_as.triggered.connect(self.saveAsLibrary)
        # actions for context menu in qtableview
        self.ui.tableView.contextMenu.deleteAction.triggered.connect(self.deleteSelectedRows)
        self.ui.tableView.contextMenu.DebugAction.triggered.connect(self.debug)
        # TODO
        self.ui.tableView.contextMenu.openAction.triggered.connect(lambda: None)
        self.ui.tableView.contextMenu.editAction.triggered.connect(lambda: None)
        # main table 
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.resizeColumnsToContents()
    
    def closeEvent(self, event):
        logger.debug("close event")
        if self.model.edited:
            messageBox = QMessageBox.warning(
                self,
                "Warning!",
                "Do you want to save changes?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            )
            if messageBox == QMessageBox.Save:
                if self.model.temporary:
                    self.saveAsLibrary()
                else:
                    self.saveLibrary()
            elif messageBox == QMessageBox.Cancel:
                event.ignore()
                return
        event.accept()
            
    # change appearance of the window title if the database is temporary
    def setTemporary(self, status: bool):
        logger.debug(f"set temporary status: {status}")
        currentTitle = self.windowTitle()
        if status:
            self.setWindowTitle(currentTitle + " (temporary)")
            self.ui.actionSave_library.setEnabled(False)
        else:
            self.setWindowTitle(currentTitle.replace(" (temporary)", ""))
            self.ui.actionSave_library.setEnabled(True)
            
    # change appearance of the window title if the database is edited
    def setEdited(self, status: bool):
        logger.debug(f"set edited status: {status}")
        currentTitle = self.windowTitle()
        if status:
            self.setWindowTitle(currentTitle + " (unsaved changes)")
        else:
            self.setWindowTitle(currentTitle.replace(" (unsaved changes)", ""))
        
    # open additional dialog windows
    def openAboutDialog(self):
        AboutDialog(self).exec()
        
    def openAddDialog(self):
        dialog = AddDialog(self)
        # if accepted add article to database and update table
        if dialog.exec() == QDialog.Accepted:
            logger.debug(f"add entry of type {type(dialog.data)}")
            self.model.addEntry(dialog.data)
            
    def deleteSelectedRows(self) -> bool:
        logger.debug(f"delete selected rows")
        rows = [r.row() for r in self.ui.tableView.selectionModel().selectedRows()]
        if len(rows)<1:
            return False
        messageBox = QMessageBox.warning(
            self,
            "Warning!",
            f"Do you want to remove the selected articles ({len(rows)})?",
            QMessageBox.Ok | QMessageBox.Cancel,
        )
        if messageBox == QMessageBox.Ok:
            self.model.removeEntriesAt(rows)
            return True
        else:
            return False
            
    def debug(self):
        logger.debug("Debug button pressed")
        author = AuthorData("John James Jacob Doe")
        author.id = 4
        entry = BookData("Test 3", [author])
        entry.id = 3
        entry.edition = 5
        self.model.addEntry(entry)     
        
        
    # file operations
    def newLibrary(self):
        logger.debug("create new db library")
        # create new temporary database
        self.model.createNewTempDB()        
        
    def openLibrary(self):
        logger.debug("open db library")
        # open file dialog and choose database to load
        fileDialog = QFileDialog(self)  
        fileDialog.setAcceptMode(QFileDialog.AcceptOpen)
        fileDialog.setNameFilter("AMT Database Files (*.amtdb)")
        if fileDialog.exec() == QFileDialog.Accepted:
            filePath = fileDialog.selectedFiles()[0]
            self.model.openExistingDB(filePath)
        
    def saveLibrary(self):
        # save current changes in cache to the database
        logger.debug("save db library")
        if not self.model.saveDB():
            logger.error("failed to save changes")
            QMessageBox.critical(
                self,
                "Error!",
                f"Failed to save changes. See log for details.",
            )
            return
        
        
    def saveAsLibrary(self):
        logger.debug("save as other file db library")
        # open file dialog and save current database to the selected file
        fileDialog = QFileDialog(self)
        fileDialog.setAcceptMode(QFileDialog.AcceptSave)
        fileDialog.setNameFilter("AMT Database Files (*.amtdb)")
        if fileDialog.exec() == QFileDialog.Accepted:
            filePath = fileDialog.selectedFiles()[0]
            if not filePath.endswith(".amtdb"):
                filePath += ".amtdb"
            self.model.saveDBAs(filePath)
            logger.info(f"Library saved as: {filePath}")
