# -*- coding: utf-8 -*-
# amt/views/arxivdialog.py

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

"""interface for submitting queries to arXiv"""

from amt.logger import getLogger
from PySide6.QtWidgets import QDialog, QProgressDialog
from PySide6.QtCore import Qt, QItemSelection, QSettings
from pathlib import Path
import amt.views.build.arxivDialog_ui as arxivDialog_ui
from amt.db.tablemodel import ArxivModel
from amt.db.datamodel import ArticleData,AuthorData
from amt.network.client import ArxivClient
from amt.network.filedownloader import EntryDownloader
from amt.network.arxiv_aux import *
from amt.network.client import ArxivRequest
from amt.views.customWidgets.amtprogress import ArxivSearchProgressDialog, MultiFileDownloadProgressDialog
from amt.views.customWidgets.amtmessagebox import AMTErrorMessageBox, AMTMutliErrorMessageBox
from amt.file_utils.linkhandler import LinkHandler
from amt.views.settingsdialog import AMTSettingsDialog

logger = getLogger(__name__)

class ArxivDialog(QDialog):
    """
    Window for searching arXiv.org for articles and adding them to the database.

    Class Attributes:
        searchOptions (dict[str, str]): A dictionary mapping search options to their respective search parameters.
        sortBys (dict[str, str]): A dictionary mapping sort by options to their respective sort by parameters.
        sortOrders (dict[str, str]): A dictionary mapping sort order options to their respective sort order parameters.
        
    Attributes:
        model (ArxivModel): The model for the table view.
        client (ArxivClient): The client for sending requests to arXiv.
        maxNumResults (int): The maximum number of results to be retrieved from arXiv.
        addingEntries (bool): A flag indicating whether entries are being added to the model
        
    Methods:
        setupUi(self) -> None
        setupModel(self) -> None
        setupClient(self) -> None
        resetUi(self) -> None
        onClientFinished(self, data: list[ArticleData]) -> None
        onSearchParametersChanged(self) -> None
        onNumResultsChanged(self, value: int) -> None
        onClientError(self, errmsg: str) -> None
        createRequest(self) -> ArxivRequest
        onLoadMoreButtonClicked(self) -> None
        onSearchButtonClicked(self) -> None
        getSelectedEntries(self) -> list[ArticleData]
        downloadEntries(self, entries: list[ArticleData]) -> None
        onSelectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None
    """
    # search options: combobox text -> search parameter
    searchOptions = {"All": ASP.ALL,
                     "Title": ASP.TITLE,
                     "Author": ASP.AUTHOR,
                     "Abstract": ASP.ABSTRACT,
                     "Comment": ASP.COMMENT,
                     "Journal": ASP.JOURNAL,
                     "Category": ASP.CATEGORY,
                     "Report": ASP.REPORT}
    # sort by options: combobox text -> sort by parameter
    sortBys = {"Submitted Date": AQSortBy.SUB,
               "Relevance": AQSortBy.REL,
               "Last Updated Date": AQSortBy.UPD}
    # sort order options: combobox text -> sort order parameter
    sortOrders = {"Descending": AQSortOrder.DESC,
                  "Ascending": AQSortOrder.ASC}
    def __init__(self, parent=None):
        super(ArxivDialog, self).__init__(parent)
        self.model = ArxivModel(self)
        self.client = ArxivClient(self)
        self.maxNumResults = 50
        self.addingEntries = False
        self.linkHandler = LinkHandler() # may be specify browser by default
        self.setupUi()
        self.setupModel()
        self.setupClient()
        self.readSettings()
        # searchQuery = ArxivSearchQuery(ASP.AUTHOR, "Juan Maldacena")
        # self.client.search(searchQuery, sort_by=AQSortBy.SUB, max_results=2)
        # self.client.send()
        # waitDialog = ArxivSearchProgressDialog(self)
        # self.client.finished.connect(waitDialog.cancel)
        # waitDialog.exec()
        
    def readSettings(self):
        settings = QSettings(AMTSettingsDialog.settingsFileName)    
        settings.beginGroup("LinkHandler")
        defLinkApp = settings.value("defLinkApp", "")
        self.linkHandler.defaultApp = defLinkApp
        httpLinkApp = settings.value("httpApp", "")
        self.linkHandler.setApp('http', httpLinkApp)
        self.linkHandler.setApp('https', httpLinkApp)
        settings.endGroup()
        
    def setupUi(self):
        """
        Sets up the UI.
        """
        self.ui: arxivDialog_ui.Ui_Dialog = arxivDialog_ui.Ui_Dialog()
        self.ui.setupUi(self)
        #self.setWindowFlag(Qt.Dialog, False)
        # make the dialog window a normal window
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        
        # default settings
        self.ui.arxivIdCheckBox.setChecked(False)
        self.ui.arxivIdLneEdit.setVisible(False)
        # add types of search
        self.ui.searchTypeComboBox.clear()
        self.ui.searchTypeComboBox.addItems([k for k in self.searchOptions.keys()])
        self.ui.searchTypeComboBox.setCurrentIndex(0)
        self.ui.sortByComboBox.clear()
        self.ui.sortByComboBox.addItems([k for k in self.sortBys.keys()])
        self.ui.sortByComboBox.setCurrentIndex(0)
        self.ui.sortOrderComboBox.clear()
        self.ui.sortOrderComboBox.addItems([k for k in self.sortOrders.keys()])
        self.ui.searchButton.clicked.connect(self.onSearchButtonClicked)
        self.ui.numResultsSpinBox.setValue(self.maxNumResults) # default value
        self.ui.numResultsSpinBox.valueChanged.connect(self.onNumResultsChanged)
        # on change of any earch parameters, disable the load more button
        self.ui.searchTypeComboBox.currentIndexChanged.connect(self.onSearchParametersChanged)
        self.ui.searchLineEdit.textChanged.connect(self.onSearchParametersChanged)
        self.ui.sortByComboBox.currentIndexChanged.connect(self.onSearchParametersChanged)
        self.ui.sortOrderComboBox.currentIndexChanged.connect(self.onSearchParametersChanged)
        self.ui.numResultsSpinBox.valueChanged.connect(self.onSearchParametersChanged)
        self.ui.arxivIdLneEdit.textChanged.connect(self.onSearchParametersChanged)
        # action buttons
        self.ui.loadMorePushButton.setEnabled(False)
        self.ui.loadMorePushButton.clicked.connect(self.onLoadMoreButtonClicked)
        self.ui.addSelectedPushButton.setEnabled(False)
        # preview
        self.ui.previewWidget.setVisible(True)
        self.ui.previewWidget.ui.previewLabel.setVisible(False)
        
    def setupModel(self):
        """
        Sets up the model for the table view.
        """
        self.ui.tableView.setModel(self.model)
        # disable sorting 
        self.ui.tableView.setSortingEnabled(False)
        # preview
        self.ui.tableView.selectionModel().selectionChanged.connect(self.onSelectionChanged)
        # context menu action
        self.ui.tableView.contextMenu.openPDFAction.triggered.connect(lambda : self.openSelected('pdf'))
        self.ui.tableView.contextMenu.openAction.triggered.connect(lambda : self.openSelected())
        # doulble click on row 
        self.ui.tableView.doubleClicked.connect(lambda : self.openSelected('pdf'))
        
        
    def setupClient(self):
        """
        Sets up the client for sending requests to arXiv.
        """
        self.client.errorEncountered.connect(self.onClientError)
        self.client.finished.connect(self.onClientFinished)
        
    def resetUi(self):
        """
        Resets the UI to the default state.
        """
        self.addingEntries = False
        self.ui.loadMorePushButton.setEnabled(False)
        self.ui.addSelectedPushButton.setEnabled(False)
        
    def onClientFinished(self, data: list[ArticleData]):
        """
        When the client finished, add the retrieved data to the model or update it.

        Args:
            data (list[ArticleData]): The data retrieved from the client.
        """
        # enable the add selected button
        self.ui.addSelectedPushButton.setEnabled(True)
        # if adding mode is enabled, add the entries to the model
        # otherwise, set the data
        if self.addingEntries:
            self.model.addEntries(data)
        else:
            self.model.setData(data)
        # determine whether more data can be loaded
        if self.client.parser.totalResults > self.model.rowCount():
            self.ui.loadMorePushButton.setEnabled(True)
        else:
            self.ui.loadMorePushButton.setEnabled(False)
        
    def onSearchParametersChanged(self):
        """
        Disables the load more button when the search parameters are changed.
        """
        self.ui.loadMorePushButton.setEnabled(False)
        
    def onNumResultsChanged(self, value: int):
        """
        Sets the maximum number of results to be retrieved from arXiv.
        Args:
            value (int): maximum entry number_
        """
        self.maxNumResults = value
        
    def onClientError(self, errmsg: str):
        """
        Displays an error message when the client encounters an error.
        Args:
            errmsg (str): error string emitted by the client.
        """
        msgbox = AMTErrorMessageBox(self)
        msgbox.setText("arxiv.org search failed.")
        msgbox.setInformativeText(errmsg)
        msgbox.exec()
        
    def createRequest(self) -> ArxivRequest:
        """
        Creates an arXiv request based on the search parameters.
        Returns:
            ArxivRequest: The request to be sent to arXiv.
        """
        request = ArxivRequest()
        searchType = self.searchOptions[self.ui.searchTypeComboBox.currentText()]
        searchValue = self.ui.searchLineEdit.text()
        searchQuery = ArxivSearchQuery(searchType, searchValue)
        sortBy = self.sortBys[self.ui.sortByComboBox.currentText()]
        sortOrder = self.sortOrders[self.ui.sortOrderComboBox.currentText()]
        request.addSearch(searchQuery)
        request.addSortBy(sortBy)   
        request.addSortOrder(sortOrder)
        maxResults = self.maxNumResults
        request.addMaxResults(maxResults)
        if self.ui.arxivIdCheckBox.isChecked():
            idList = [id.strip() for id in self.ui.arxivIdLneEdit.text().split(",")]
            request.addArxivId(idList)
        return request
        
    def onLoadMoreButtonClicked(self):
        """
        Sends a request to arXiv to load more entries.
        """
        self.addingEntries = True
        request = self.createRequest()
        request.addStart(self.model.rowCount())
        self.client.request = request   
        self.client.send()
        waitDialog = ArxivSearchProgressDialog(self)
        self.client.finished.connect(waitDialog.cancel)
        waitDialog.exec()
        
    def onSearchButtonClicked(self):
        """
        Sends a request to arXiv based on the search parameters.
        """
        self.resetUi()
        request = self.createRequest()
        self.client.request = request
        self.client.send()
        waitDialog = ArxivSearchProgressDialog(self)
        self.client.finished.connect(waitDialog.cancel)
        waitDialog.exec()
        
    def getSelectedEntries(self) -> list[ArticleData]:
        """
        Gets the selected entries in the table view. If the download pdfs checkbox is checked, the entries are downloaded.
        Returns:
            list[ArticleData]: The selected entries.
        """
        selectedRows = self.ui.tableView.selectionModel().selectedRows()
        selectedEntries: list[ArticleData] = []
        for row in selectedRows:
            selectedEntries.append(self.model.getDataAt(row.row()))
        if self.ui.downloadPdfsCheckBox.isChecked():   
            self.downloadEntries(selectedEntries)
        return selectedEntries
    
    def downloadEntries(self, entries: list[ArticleData]):
        """
        Downloads the pdfs of the selected entries.

        Args:
            entries (list[ArticleData]): entries to download.
        """
        downloader = EntryDownloader(self)
        waitDialog = MultiFileDownloadProgressDialog(self)
        downloader.downloadProgressed.connect(waitDialog.setMultiValue)
        downloader.downloadFinished.connect(waitDialog.cancel)
        downloader.downloadFinishedWithErrors.connect(
                lambda errs: AMTMutliErrorMessageBox(
                    self, 
                    text = "One or multiple download(s) failed:", 
                    errors=errs).exec()
                )
        for entry in entries:
            downloader.addDownloadEntry(entry)
        if downloader.startDownload():
            waitDialog.exec()
        else:
            waitDialog.cancel()
        

    def onSelectionChanged(self, selected: QItemSelection, deselected: QItemSelection):
        """     
        Updates the preview with the selected entry.
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
             
    def openSelected(self, target = 'arxiv'):
        logger.debug("open pdf triggered")
        rows = self.ui.tableView.selectionModel().selectedRows()
        if len(rows) < 1:
            logger.info("No rows selected")
            return 
        entry = self.model.getDataAt(rows[0].row())
        # TODO: all entries are neccessarily arxiv entries: fix it
        if not isinstance(entry, ArticleData):
            return
        else:
            if target == 'arxiv':
                self.linkHandler.openLink(entry.link)
            elif target == 'pdf':
                self.linkHandler.openLink(entry.filelink)
            else:
                logger.error(f"Unknown target {target}")
        return
        