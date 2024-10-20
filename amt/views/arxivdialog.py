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
from PySide6.QtWidgets import QDialog
import amt.views.build.arxivDialog_ui as arxivDialog_ui
from amt.db.tablemodel import ArxivModel
from amt.db.datamodel import ArticleData,AuthorData
from amt.network.client import ArxivClient
from amt.network.arxiv_aux import *

logger = getLogger(__name__)

class ArxivDialog(QDialog):
    def __init__(self, parent=None):
        super(ArxivDialog, self).__init__(parent)
        self.model = ArxivModel(self)
        self.client = ArxivClient(self)
        self.setupUi()
        self.client.finished.connect(self.model.addEntries)
        searchQuery = ArxivSearchQuery(ASP.AUTHOR, "Juan Maldacena")
        self.client.search(searchQuery, sort_by=AQSortBy.SUB, max_results=100)
        self.client.send()
        
    def setupUi(self):
        self.ui: arxivDialog_ui.Ui_Dialog = arxivDialog_ui.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.tableView.setModel(self.model)
        
        

