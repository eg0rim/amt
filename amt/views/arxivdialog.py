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
from PySide6.QtCore import Qt, QItemSelection
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

logger = getLogger(__name__)

class ArxivDialog(QDialog):
    searchOptions = {"All": ASP.ALL,
                     "Title": ASP.TITLE,
                     "Author": ASP.AUTHOR,
                     "Abstract": ASP.ABSTRACT,
                     "Comment": ASP.COMMENT,
                     "Journal": ASP.JOURNAL,
                     "Category": ASP.CATEGORY,
                     "Report": ASP.REPORT}
    sortBys = {"Submitted Date": AQSortBy.SUB,
               "Relevance": AQSortBy.REL,
               "Last Updated Date": AQSortBy.UPD}
    sortOrders = {"Descending": AQSortOrder.DESC,
                  "Ascending": AQSortOrder.ASC}
    def __init__(self, parent=None):
        super(ArxivDialog, self).__init__(parent)
        self.model = ArxivModel(self)
        self.client = ArxivClient(self)
        self.downloader = EntryDownloader(self)
        self.maxNumResults = 50
        self.addingEntries = False
        self.setupUi()
        self.setupModel()
        self.setupClient()
        # searchQuery = ArxivSearchQuery(ASP.AUTHOR, "Juan Maldacena")
        # self.client.search(searchQuery, sort_by=AQSortBy.SUB, max_results=2)
        # self.client.send()
        # waitDialog = ArxivSearchProgressDialog(self)
        # self.client.finished.connect(waitDialog.cancel)
        # waitDialog.exec()
        
    def setupUi(self):
        self.ui: arxivDialog_ui.Ui_Dialog = arxivDialog_ui.Ui_Dialog()
        self.ui.setupUi(self)
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
        self.ui.tableView.setModel(self.model)
        # disable sorting 
        self.ui.tableView.setSortingEnabled(False)
        # disable context menu in the table view
        self.ui.tableView.setContextMenuPolicy(Qt.NoContextMenu)
        # preview
        self.ui.tableView.selectionModel().selectionChanged.connect(self.onSelectionChanged)
        
    def setupClient(self):
        self.client.errorEncountered.connect(self.onClientError)
        self.client.finished.connect(self.onClientFinished)
        
    def resetUi(self):
        self.addingEntries = False
        self.ui.loadMorePushButton.setEnabled(False)
        self.ui.addSelectedPushButton.setEnabled(False)
        
    def onClientFinished(self, data: list[ArticleData]):
        self.ui.addSelectedPushButton.setEnabled(True)
        if self.addingEntries:
            self.model.addEntries(data)
        else:
            self.model.setData(data)
        if self.client.parser.totalResults > self.model.rowCount():
            self.ui.loadMorePushButton.setEnabled(True)
        else:
            self.ui.loadMorePushButton.setEnabled(False)
        
    def onSearchParametersChanged(self):
        self.ui.loadMorePushButton.setEnabled(False)
        
    def onNumResultsChanged(self, value: int):
        self.maxNumResults = value
        
    def onClientError(self, errmsg: str):
        msgbox = AMTErrorMessageBox(self)
        msgbox.setText("arxiv.org search failed.")
        msgbox.setInformativeText(errmsg)
        msgbox.exec()
        
    def parseRequest(self) -> ArxivRequest:
        request = ArxivRequest()
        searchType = self.searchOptions[self.ui.searchTypeComboBox.currentText()]
        searchValue = self.ui.searchLineEdit.text()
        searchQuery = ArxivSearchQuery(searchType, searchValue)
        sortBy = self.sortBys[self.ui.sortByComboBox.currentText()]
        sortOrder = self.sortOrders[self.ui.sortOrderComboBox.currentText()]
        request.addSearch(searchQuery)
        request.addSortBy(sortBy)   
        request.addSortOrder(sortOrder)
        maxResults = self.ui.numResultsSpinBox.value()
        request.addMaxResults(maxResults)
        if self.ui.arxivIdCheckBox.isChecked():
            idList = [id.strip() for id in self.ui.arxivIdLneEdit.text().split(",")]
            request.addArxivId(idList)
        return request
        
    def onLoadMoreButtonClicked(self):
        self.addingEntries = True
        request = self.parseRequest()
        request.addStart(self.model.rowCount())
        self.client.request = request   
        self.client.send()
        waitDialog = ArxivSearchProgressDialog(self)
        self.client.finished.connect(waitDialog.cancel)
        waitDialog.exec()
        
    def onSearchButtonClicked(self):
        self.resetUi()
        request = self.parseRequest()
        self.client.request = request
        self.client.send()
        waitDialog = ArxivSearchProgressDialog(self)
        self.client.finished.connect(waitDialog.cancel)
        waitDialog.exec()
        
    def getSelectedEntries(self) -> list[ArticleData]:
        selectedRows = self.ui.tableView.selectionModel().selectedRows()
        selectedEntries: list[ArticleData] = []
        for row in selectedRows:
            selectedEntries.append(self.model.getDataAt(row.row()))
        if self.ui.downloadPdfsCheckBox.isChecked():  
            waitDialog = MultiFileDownloadProgressDialog(self)            
            logger.debug(f"Downloading {len(selectedEntries)} files")
            for entry in selectedEntries:
                logger.debug(f"Adding entry to download queue: {entry.title}")
                self.downloader.addDownloadEntry(entry)
            self.downloader.downloadProgressed.connect(waitDialog.setMultiValue)
            self.downloader.downloadFinished.connect(waitDialog.cancel)
            self.downloader.downloadFinishedWithErrors.connect(
                lambda errs: AMTMutliErrorMessageBox(self, text = "One or multiple download(s) failed:", errors=errs).exec()
                )
            self.downloader.startDownload()
            waitDialog.exec()
        return selectedEntries
    

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