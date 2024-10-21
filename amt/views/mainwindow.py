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

import sys, subprocess
from PySide6.QtCore import QSettings, QSize, QItemSelection, Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QDialog,
    QFileDialog,
    QLabel
)
from PySide6.QtGui import QIcon, QPixmap
from amt.db.tablemodel import AMTDBModel, AMTFilter
from amt.db.database import AMTDatabaseError
from amt.db.datamodel import (
    ArticleData, 
    AuthorData, 
    BookData, 
    LecturesData
)
from PySide6.QtNetwork import QNetworkRequest, QNetworkAccessManager

from amt.views.customWidgets.amtfiledialog import AMTDBFileDialog

from  .build.resources_qrc import *
from .build.mainwindow_ui import (
    Ui_MainWindow
)

from .aboutdialog import AboutDialog
from .adddialog import AddDialog
from .settingsdialog import AMTSettingsDialog
from .arxivdialog import ArxivDialog

from amt.logger import getLogger
from amt.views.customWidgets.amtmessagebox import (
    AMTErrorMessageBox,
    AMTWarnMessageBox,
    AMTCriticalMessageBox,
    AMTInfoMessageBox,
    AMTQuestionMessageBox
)
from amt.file_utils.filehandler import ExternalEntryHandler, ApplicationNotSetError
from amt.network.arxiv_aux import *
from amt.network.client import ArxivClient

logger = getLogger(__name__)

class MainWindow(QMainWindow):
    """
    MainWindow class represents the main window of the application.
    This class is responsible for initializing and managing the main window, including setting up the user interface,
    handling settings, controlling the model-view architecture, and providing main functionalities such as searching, and managing library entries.
    Attributes:
        currentFile (str): The current database file name.
        ui (Ui_MainWindow): The user interface object for the main window. Generated from the .ui file. Contains all the widgets and actions.
        model (AMTDBModel): The model for the table view.
        fileHandler (ExternalEntryHandler): The file handler object for opening external files.
        openEntriesOnStartup (bool): The flag indicating whether to open entries on startup.
        closeEntriesOnExit (bool): The flag indicating whether to close entries on exit.
        dbFileDialog (AMTDBFileDialog): The file dialog for opening and saving database files.
    Methods:
        __init__(self, parent=None):
        readSettings(self):
        readState(self):
        writeState(self):
        setupUI(self):
        setTemporary(self, status: bool):
        setEdited(self, status: bool):
        setupModelView(self):
        setupSearchBar(self):
        closeEvent(self, event):
        toggleSearchBar(self):
        search(self, index, pattern, useRegex):
        updateTable(self):
        openSelectedRowsExternally(self) -> bool:
        deleteSelectedRows(self) -> bool:
        editSelectedRow(self) -> bool:
        openAddDialog(self):
        openSettingsDialog(self):
        openAboutDialog(self):
        openArxivDialog(self):
        updatePreview(self, selected: QItemSelection, deselected: QItemSelection):
        onDatabaseConnected(self, name: str):
        setCurrentFile(self, file: str):
        newLibrary(self):
        openLibrary(self):
        saveLibrary(self):
        saveAsLibrary(self):
    """
    stateFile = "AMT/AMTState"
    def __init__(self, parent=None):
        """
        Initializes the main window.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        # attributes:
        # current file name
        self.currentFile: str = ""
        # ui
        self.ui: Ui_MainWindow = None
        # model for the table view
        self.model: AMTDBModel = None
        # file handler
        self.fileHandler: ExternalEntryHandler = ExternalEntryHandler()
        # settings atrbiutes
        self.openEntriesOnStartup: bool = False
        self.closeEntriesOnExit: bool = False
        # file dialogs
        self.dbFileDialog = AMTDBFileDialog(self) 
        # arxiv dialog
        self.arxivDialog = ArxivDialog(self)   
        # setup main window
        # setup ui
        self.setupUI()      
        # create model
        self.setupModelView()    
        # setup searchbar
        self.setupSearchBar()
        # if no filename is loaded, set temporary status
        if self.currentFile:
            self.setTemporary(False)
        else:
            self.setTemporary(True)
        # final setup
        # load settings
        self.readSettings()
        # reproduce the state of the app before last closing
        self.readState()
        # at the start no changes are made
        self.setEdited(False)
        # if no filename is loaded, set temporary status
        if self.currentFile:
            self.setTemporary(False)
        else:
            self.setTemporary(True)
        logger.info("Main window is initialized.")

    
    # read and write settings
    def readSettings(self):
        """
        Reads and restores the application settings from the QSettings storage.

        This method retrieves and applies the saved settings for the main window's
        geometry and state, as well as the last used database file. If no settings
        are found, default values are used.
        """
        settings = QSettings(AMTSettingsDialog.settingsFileName)       
        settings.beginGroup("FileHandler")
        defAppFile = settings.value("defaultAppFile", "")
        self.fileHandler.defaultApp = defAppFile
        pdfApp = settings.value("pdfApp", "")
        self.fileHandler.setApp("pdf", pdfApp)
        djvuApp = settings.value("djvuApp", "")
        self.fileHandler.setApp("djvu", djvuApp)
        self.openEntriesOnStartup = settings.value("openEntriesOnStartup", False, type = bool)
        self.closeEntriesOnExit = settings.value("closeEntriesOnExit", False,type = bool)
        settings.endGroup()
        
        settings.beginGroup("Preview")
        width = settings.value("previewWidth", 300, type = int)
        height = settings.value("previewHeight", 400, type = int)
        self.ui.previewWidget.setPreviewSize(width, height)
        #self.ui.previewWidget.setVisible(settings.value("showPreviewOnStartup", False, type = bool))
        settings.endGroup()
        
    def readState(self):
        settings = QSettings(self.stateFile)
        # read window settings
        settings.beginGroup("MainWindow")
        self.restoreGeometry(settings.value("geometry"))
        self.ui.splitter.restoreState(settings.value("splitterState"))
        self.ui.previewWidget.setVisible(settings.value("previewOn", False, type = bool))
        #self.restoreState(settings.value("state"))
        #self.resize(settings.value("windowSize", self.size()))
        settings.endGroup()
        # read database settings
        settings.beginGroup("Database")
        # retrieve last used filename; if empty, set empty filename => temporary status
        self.currentFile = settings.value("lastUsedFile", "")
        if self.currentFile:
            self.model.openExistingDB(self.currentFile)
        settings.endGroup()
        settings.beginGroup("FileHandler")
        # open files opened last time
        if self.openEntriesOnStartup:
            openFiles = settings.value("openFiles", [], type = list)
            for file in openFiles:
                self.fileHandler.openFile(file)
        settings.endGroup()
        
        settings.beginGroup("TableView")
        sortingColumn = settings.value("sortingColumn", 0, type = int)
        sortingOrder = settings.value("sortingOrder", Qt.AscendingOrder)
        self.ui.tableView.horizontalHeader().setSortIndicator(sortingColumn, sortingOrder)
        settings.endGroup()
        
        settings.beginGroup("ArxivDialog")
        self.arxivDialog.ui.searchTypeComboBox.setCurrentIndex(settings.value("searchType", 0, type = int))
        self.arxivDialog.ui.arxivIdCheckBox.setChecked(settings.value("arxivIdCheckBox", False, type = bool))
        self.arxivDialog.ui.splitter.restoreState(settings.value("splitterState"))
        self.arxivDialog.restoreGeometry(settings.value("geometry"))
        settings.endGroup()
        
    def writeState(self):
        settings = QSettings(self.stateFile)
        settings.beginGroup("MainWindow")
        # TODO: size does not save
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("splitterState", self.ui.splitter.saveState())
        settings.setValue("previewOn", self.ui.previewWidget.isVisible())
        #settings.setValue("state", self.saveState())
        #settings.setValue("windowSize", self.size())
        settings.endGroup()
        
        settings.beginGroup("Database")
        settings.setValue("lastUsedFile", self.currentFile)
        settings.endGroup()
        
        settings.beginGroup("FileHandler")
        settings.setValue("openFiles", list(self.fileHandler.getOpenedFiles()))
        settings.endGroup()
        
        settings.beginGroup("TableView")
        settings.setValue("sortingColumn", self.ui.tableView.horizontalHeader().sortIndicatorSection())
        settings.setValue("sortingOrder", self.ui.tableView.horizontalHeader().sortIndicatorOrder())
        settings.endGroup()
        
        settings.beginGroup("ArxivDialog")
        settings.setValue("searchType", self.arxivDialog.ui.searchTypeComboBox.currentIndex())
        settings.setValue("arxivIdCheckBox", self.arxivDialog.ui.arxivIdCheckBox.isChecked())
        settings.setValue("splitterState", self.arxivDialog.ui.splitter.saveState())
        settings.setValue("geometry", self.arxivDialog.saveGeometry())
        settings.endGroup()
 
    # setup methods        
    def setupUI(self):
        """
        Sets up the user interface for the main window.

        This method initializes the UI components, sets icons for various actions,
        connects signals to their respective slots, and hides unused widgets.
        """
        # setup ui
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # set icons
        self.setWindowIcon(QIcon(":/logo")) # does not work
        #self.setIconSize(QSize(16, 16))
        self.ui.actionAdd.setIcon(QIcon(":/icons/add"))
        self.ui.actionDel.setIcon(QIcon(":/icons/remove"))
        self.ui.actionEdit.setIcon(QIcon(":/icons/edit"))
        self.ui.actionUpdate.setIcon(QIcon(":/icons/update"))
        self.ui.actionSaveLibrary.setIcon(QIcon(":/icons/save"))
        self.ui.actionSaveAs.setIcon(QIcon(":/icons/saveas"))
        self.ui.actionNewLibrary.setIcon(QIcon(":/icons/new"))
        self.ui.actionOpenLibrary.setIcon(QIcon(":/icons/open"))
        self.ui.actionSearch.setIcon(QIcon(":/icons/search"))
        self.ui.actionQuit.setIcon(QIcon(":/icons/quit"))
        self.ui.actionAbout.setIcon(QIcon(":/icons/about"))
        self.ui.actionDebug.setIcon(QIcon(":/icons/bug"))
        self.ui.actionUpdate.setIcon(QIcon(":/icons/update"))
        self.ui.actionSettings.setIcon(QIcon(":/icons/settings"))
        self.ui.actionPreview.setIcon(QIcon(":/icons/preview"))
        self.ui.actionArxiv.setIcon(QIcon(":/icons/arxiv"))
        # connect signals
        # actions in toolbar
        # add entry
        self.ui.actionAdd.triggered.connect(self.openAddDialog)
        # debug button
        self.ui.actionDebug.triggered.connect(self.debug)
        # delete entries
        self.ui.actionDel.triggered.connect(self.deleteSelectedRows)
        # retrieve data from database
        self.ui.actionUpdate.triggered.connect(self.updateTable)
        # edit entry
        self.ui.actionEdit.triggered.connect(self.editSelectedRow)
        # show search bar
        self.ui.actionSearch.triggered.connect(self.toggleSearchBar)
        # show preview
        self.ui.actionPreview.triggered.connect(self.ui.previewWidget.toggleVisibility)
        # actions in menu
        # quit application
        self.ui.actionQuit.triggered.connect(self.close)
        # open about window
        self.ui.actionAbout.triggered.connect(self.openAboutDialog)
        # create new db
        self.ui.actionNewLibrary.triggered.connect(self.newLibrary)
        # open existing db
        self.ui.actionOpenLibrary.triggered.connect(self.openLibrary)
        # save current database
        self.ui.actionSaveLibrary.triggered.connect(self.saveLibrary)
        # save current database as another file
        self.ui.actionSaveAs.triggered.connect(self.saveAsLibrary)
        # settings 
        self.ui.actionSettings.triggered.connect(self.openSettingsDialog)
        # arxiv
        self.ui.actionArxiv.triggered.connect(self.openArxivDialog)
        # actions in table
        # open entry on double click
        self.ui.tableView.doubleClicked.connect(self.openSelectedRowsExternally) 
        # open entry on context menu
        self.ui.tableView.contextMenu.openAction.triggered.connect(self.openSelectedRowsExternally)
        # edit entry on context menu
        self.ui.tableView.contextMenu.editAction.triggered.connect(self.editSelectedRow)
        # delete entry on context menu
        self.ui.tableView.contextMenu.deleteAction.triggered.connect(self.deleteSelectedRows)   
        # arxiv dialog
        self.arxivDialog.ui.addSelectedPushButton.clicked.connect(self.addFromArxivDialog)
        # hide unused widgets
        self.ui.actionDebug.setVisible(False)
               
    def setTemporary(self, status: bool):
        """
        Updates the window title to indicate a temporary status and enables/disables the save library action.

        Args:
            status (bool): If True, appends " (temporary)" to the window title and disables the save library action.
                   If False, removes " (temporary)" from the window title and enables the save library action.
        """
        currentTitle = self.windowTitle()
        if status:
            self.setWindowTitle(currentTitle + " (temporary)")
            self.ui.actionSaveLibrary.setEnabled(False)
        else:
            self.setWindowTitle(currentTitle.replace(" (temporary)", ""))
            self.ui.actionSaveLibrary.setEnabled(True)
            
    def setEdited(self, status: bool):
        """
        Updates the window title to indicate whether there are unsaved changes.

        Args:
            status (bool): If True, appends " (unsaved changes)" to the current window title.
                           If False, removes " (unsaved changes)" from the current window title.
        """
        currentTitle = self.windowTitle()
        if status:
            self.setWindowTitle(currentTitle + " (unsaved changes)")
        else:
            self.setWindowTitle(currentTitle.replace(" (unsaved changes)", ""))
            
    def setupModelView(self):
        """
        Sets up the model-view architecture for the main window.
        """
        # create model based on current filename
        # if db raises error, show critical message box and close the app
        try:
            self.model = AMTDBModel(self.currentFile)
            logger.info(f"Model is connected.")
        except AMTDatabaseError:
            logger.critical(f"Database Error: {self.model.db.lastError().text()}")
            msgBox = AMTCriticalMessageBox(self)
            msgBox.setText("Critical Error! AMT will be closed.")
            msgBox.setInformativeText(f"Database Error: {self.model.db.lastError().text()}")
            msgBox.exec()
            sys.exit(1)
        # bind model to table view
        self.ui.tableView.setModel(self.model)
        # retrieve data from database
        self.model.update()
        # resize columns to fit content
        self.ui.tableView.resizeColumnsToContents()
        # connect signals
        # model handles file management and keeps track changes in cache
        # if db file is temporary, set temporary status
        self.model.temporaryStatusChanged.connect(self.setTemporary)
        # if cache diverged, set edited status
        self.model.dataCache.cacheDiverged.connect(self.setEdited)
        # if db is connected, set current file
        self.model.databaseConnected.connect(self.onDatabaseConnected)
        # if selection changed
        self.ui.tableView.selectionModel().selectionChanged.connect(self.updatePreview)
        
    def setupSearchBar(self):
        """
        Sets up search bar based on the model's column names.
        """
        self.ui.searchInput.addColumns(self.model._columnNames)
        # connect search signal
        self.ui.searchInput.searchInputChanged.connect(self.search)
        
    # event methods
    def closeEvent(self, event):
        """
        Handles the close event for the main window.

        Parameters:
        event (QCloseEvent): The close event triggered when the window is requested to close.
        """
        # if the model has unsaved changes, ask user if they want to save them
        logger.info("Close event triggered.")
        if self.model.dataCache.diverged:
            msgBox = AMTQuestionMessageBox(self)
            msgBox.setText("Do you want to save changes before closing?")
            msgBox.setInformativeText("All unsaved changes will be lost.")
            msgBox.setStandardButtons(
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            )
            ret = msgBox.exec()
            if ret == QMessageBox.Save:
                if self.model.temporary:
                    # for temporary db, save as a new file
                    self.saveAsLibrary()
                else:
                    # for existing db, save changes inplace
                    self.saveLibrary()
            elif ret == QMessageBox.Cancel:
                event.ignore()
                return
        # check if there are open files
        # and update the dictionary of open files
        self.fileHandler.syncFiles()
        # save settings
        self.writeState()
        # close all open files
        if self.closeEntriesOnExit:
            self.fileHandler.closeAllFiles()
        logger.info("Exiting app.")
        event.accept()
        
    # search methods      
    def toggleSearchBar(self):
        """
        Toggles the visibility of the search bar and resets its input field.
        """
        logger.info("Search bar toggled.")
        self.ui.searchInput.reset()
        self.ui.searchInput.toggleVisible()  
        
    def search(self, index, pattern, useRegex):
        """
        Searches for a pattern in the specified column(s) of the model.

        Args:
            index (int): The index of the filterComboBox option.
            pattern (str): The search pattern to look for.
            useRegex (bool): If True, the pattern is treated as a regular expression.
        """
        # search fieldsComboBox has an additional first item compared to the model's column names
        # that corresponds to searching in all visible columns
        fieldsIndex = index - 1
        if fieldsIndex == -1 : 
            fields = self.model._columnToField.values()
        else:
            fields = self.model._columnToField[fieldsIndex]
        # create filter object corresponding to the search parameters
        filter = AMTFilter(fields, pattern, not useRegex)
        # apply filter to the model
        self.model.filter(filter)       
    
    # manage entries
    def updateTable(self):
        """
        Updates the model with the data from the database.
        All unsaved changes will be lost.
        """
        if self.model.dataCache.diverged:
            # warn that changes will be lost
            msgBox = AMTQuestionMessageBox(self)
            msgBox.setText("Do you want to update the table?")
            msgBox.setInformativeText("All unsaved changes will be lost.")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ret = msgBox.exec()
            if ret == QMessageBox.Cancel:
                return
        # retrieve data from database
        self.model.update()
        self.ui.previewWidget.reset()
        
    def openSelectedRowsExternally(self) -> bool:
        """
        Opens the selected rows.
        
        Returns:
            bool: True if all selected entries are opened successfully, False otherwise.
        """
        state = True
        rows = [r.row() for r in self.ui.tableView.selectionModel().selectedRows()]
        if len(rows)<1:
            return False
        # if multiple rows selected, ask user if they want to open all of them
        if len(rows)>1:
            msgBox = AMTInfoMessageBox(self)
            msgBox.setText("Multiple entries are selected.")
            msgBox.setInformativeText("Do you want to open all of them?")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ret = msgBox.exec()       
            if ret == QMessageBox.Cancel:
                return False
        # open each entry in the cycle
        for row in rows:
            entry = self.model.getDataAt(row)
            msgBox = None
            try:
                self.fileHandler.openEntry(entry)
            except FileNotFoundError as e:
                msgBox = AMTErrorMessageBox(self)
                msgBox.setText("Can not open the entry.")
                msgBox.setInformativeText(str(e))
                state = False
            except ApplicationNotSetError as e:
                msgBox = AMTErrorMessageBox(self)
                msgBox.setText(f"No application set to open {e.fileType} files.")
            except Exception as e:
                msgBox = AMTErrorMessageBox(self)
                msgBox.setText("Error occurred while opening the entry.")
                msgBox.setInformativeText(f"Error: {e}")
                msgBox.exec()
                state = False
            if msgBox:
                msgBox.exec()
        return state
                
    def deleteSelectedRows(self) -> bool:
        """
        Deletes the selected rows from the model

        Returns:
            bool: True if the selected rows were successfully deleted, False otherwise.
        """
        rows = [r.row() for r in self.ui.tableView.selectionModel().selectedRows()]
        if len(rows)<1:
            return False
        # ask user if they want to remove selected entries
        msgBox = AMTQuestionMessageBox(self)
        msgBox.setText(f"Do you want to remove selected entries ({len(rows)})?")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        ret = msgBox.exec()
        if ret == QMessageBox.Ok:
            self.model.removeEntriesAt(rows)
            return True
        else:
            return False        
        
    def editSelectedRow(self) -> bool:
        """
        Edit the selected row in the table view.

        Returns:
            bool: True if the row was successfully edited, False otherwise.
        """
        rows = [r.row() for r in self.ui.tableView.selectionModel().selectedRows()]
        # do not allow to edit multiple rows at once
        if len(rows) != 1:
            msgBox = AMTInfoMessageBox(self)
            msgBox.setText("Please select only one row to edit.")
            msgBox.exec()
            return False
        # use the same dialog for adding and editing
        # perhaps, to be reconsidered in the future
        entry = self.model.getDataAt(rows[0])
        dialog = AddDialog(entryToEdit=entry, parent=self)
        #dialog.setData(self.model.dataCache.data[rows[0]])
        if dialog.exec() == QDialog.Accepted:
            self.model.editEntryAt(rows[0], dialog.data)
            return True
        else:
            return False
        
    def addFromArxivDialog(self):
        entries = self.arxivDialog.getSelectedEntries()
        if entries:
            self.model.addEntries(entries)
    
    def openAddDialog(self):
        """
        Opens the AddDialog for adding a new article entry.
        If the dialog is accepted, the article is added to the database.
        """
        dialog = AddDialog(self)
        # if accepted add article to database
        if dialog.exec() == QDialog.Accepted:
            self.model.addEntry(dialog.data)
            logger.debug(f"Added entry to the database: {repr(dialog.data.title)}")
            
    def openSettingsDialog(self):
        """ 
        Opens settings dialog.
        """
        dialog = AMTSettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.readSettings()
            
    def openArxivDialog(self):
        """
        Opens arXiv dialog for submitting queries.
        """
        self.arxivDialog.show()
         
    # open additional dialog windows
    def openAboutDialog(self):
        """
        Opens about dialog. Attributions and license information are displayed.
        """
        AboutDialog(self).exec()
        
    def updatePreview(self, selected: QItemSelection, deselected: QItemSelection):
        """     
        Updates the preview label with the selected entry.
        Args:
            selected (QItemSelection): The selected items in the table view.
            deselected (QItemSelection): The deselected items in the table view.
        """
        try:
            row = selected.indexes()[0].row()
        except IndexError:
            row = deselected.indexes()[0].row()
        entry = self.model.getDataAt(row)
        if entry:
             self.ui.previewWidget.setEntry(entry)
                
    def onDatabaseConnected(self, name: str):
        """
        Updates the current file name and clears the preview cache.
        """
        self.setCurrentFile(name)
        self.ui.previewWidget.clearCache()
    
    # file operations
    def setCurrentFile(self, file: str):
        """
        Sets the current file for the model. For temporary databases, the current file is set to an empty string.

        Args:
            file (str): The file path to set as the current file.
        """

        if self.model.temporary:
            self.currentFile = ""
        else:
            self.currentFile = file
            
    def newLibrary(self):
        """
        Creates new temporary database.
        """
        self.model.createNewTempDB()   
        
    def openLibrary(self):
        """
        Opens existing database.
        """
        # open file dialog and choose database to load
        self.dbFileDialog.setAcceptMode(QFileDialog.AcceptOpen)
        if self.dbFileDialog.exec() == QFileDialog.Accepted:
            filePath = self.dbFileDialog.selectedFile()
            self.model.openExistingDB(filePath)
        
    def saveLibrary(self):
        """
        Saves current changes in cache to the database.
        """
        if not self.model.saveDB():
            logger.error("failed to save changes")
            msgBox = AMTErrorMessageBox(self)
            msgBox.setText("Failed to save changes.")
            msgBox.setInformativeText("See logs for details.")
            msgBox.exec()
            return
        
    def saveAsLibrary(self):
        """
        Saves current changes in cache to a new file.
        """
        self.dbFileDialog.setAcceptMode(QFileDialog.AcceptSave)
        if self.dbFileDialog.exec() == QFileDialog.Accepted:
            filePath = self.dbFileDialog.selectedFile()
            if not self.model.saveDBAs(filePath):
                logger.error("failed to save changes in new file")
                msgBox = AMTErrorMessageBox(self)
                msgBox.setText("Failed to save changes in new file.")
                msgBox.setInformativeText("See logs for details.")
                msgBox.exec()
                return
             
    def debug(self):
        logger.debug("Debug button pressed")
