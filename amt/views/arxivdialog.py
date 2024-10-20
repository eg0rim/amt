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
import amt.views.build.arxivDialog_ui as arxivDialog_ui
from amt.db.tablemodel import ArxivModel
from amt.db.datamodel import ArticleData,AuthorData
from amt.network.client import ArxivClient
from amt.network.arxiv_aux import *
from amt.network.client import ArxivRequest
from amt.views.customWidgets.amtprogress import ArxivSearchProgressDialog

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
        self.maxNumResults = 10
        self.addingEntries = False
        self.setupUi()
        self.setupModel()
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
        # action buttons
        self.ui.loadMorePushButton.setEnabled(False)
        self.ui.loadMorePushButton.clicked.connect(self.onLoadMoreButtonClicked)
        self.ui.addSelectedPushButton.setEnabled(False)
        
    def setupModel(self):
        self.ui.tableView.setModel(self.model)
        self.client.finished.connect(self.onClientFinished)
        # disable sorting 
        self.ui.tableView.setSortingEnabled(False)
        
    def resetUi(self):
        self.addingEntries = False
        self.ui.loadMorePushButton.setEnabled(False)
        
    def onClientFinished(self, data: list[ArticleData]):
        if self.addingEntries:
            self.model.addEntries(data)
        else:
            self.model.setData(data)
        if self.client.parser.totalResults > self.model.rowCount():
            self.ui.loadMorePushButton.setEnabled(True)
        else:
            self.ui.loadMorePushButton.setEnabled(False)
        
        
    def onNumResultsChanged(self, value: int):
        self.maxNumResults = value
        
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
        

