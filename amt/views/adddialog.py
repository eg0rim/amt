# -*- coding: utf-8 -*-
# amt/views/adddialog.py

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

"""add dialog window"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QDialogButtonBox,
    QMessageBox
)
from PySide6.QtGui import *
import urllib.request

from amt.parser.parser import parseArxiv

class AddDialog(QDialog):
    """add dialog."""
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle("Add article")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.data = None
        self.titleField = QLineEdit()
        self.authorsField = QLineEdit()
        self.arxivIdField = QLineEdit()
        self.versionField = QLineEdit()
        self.datePublishedField = QLineEdit()
        self.dateUpdatedField = QLineEdit()
        self.linkField = QLineEdit()
        self.arxivButton = QPushButton("Get metadata")
        self.arxivButton.clicked.connect(self.getMetadataFromArxiv)
        self.setupUI()

    def setupUI(self):
        """setup the add window UI"""
        # fields to enter arxiv id

        self.titleField.setObjectName("title")
        self.authorsField.setObjectName("authors")
        self.arxivIdField.setObjectName("arxiv_id")
        self.versionField.setObjectName("version")
        self.datePublishedField.setObjectName("date_published")
        self.dateUpdatedField.setObjectName("date_updated")
        self.linkField.setObjectName("link")
        
        # Lay out the data fields
        layout = QFormLayout()
        layout.addRow("Title:", self.titleField)
        layout.addRow("Authors:", self.authorsField)
        layout.addRow("arXiv id:", self.arxivIdField)
        layout.addRow("Version:", self.versionField)
        layout.addRow("Date published:", self.datePublishedField)
        layout.addRow("Date updated:", self.dateUpdatedField)
        layout.addRow("Link:", self.linkField)
        self.layout.addLayout(layout)
        # Add button to parse data from arxiv
        self.layout.addWidget(self.arxivButton)
        # Add standard buttons to the dialog and connect them
        self.buttonsBox = QDialogButtonBox(self)
        self.buttonsBox.setOrientation(Qt.Horizontal)
        self.buttonsBox.setStandardButtons(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.buttonsBox.accepted.connect(self.accept)
        self.buttonsBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonsBox)

    def getMetadataFromArxiv(self):
        if not self.arxivIdField.text():
            QMessageBox.critical(
                self,
                "Error!",
                f"You must provide arxiv id",
            )
            return
        try:
            data = parseArxiv(self.arxivIdField.text())
        except urllib.error.URLError:
            QMessageBox.critical(
                self,
                "Error!",
                f"Check your internet connection",
            )
            return
        if not data:
            QMessageBox.critical(
                self,
                "Error!",
                f"Article not found! Check the arXiv id",
            )
            return
        self.titleField.setText(data['title'])
        self.authorsField.setText(', '.join(data['authors']))
        self.arxivIdField.setText(data['arxiv_id'])
        self.versionField.setText(data['version'])
        self.datePublishedField.setText(data['date_published'])
        self.dateUpdatedField.setText(data['date_updated'])
        self.linkField.setText(data['link'])


    def accept(self):
        """Accept the data provided through the dialog."""
        self.data = {}
        if not self.titleField.text():
            QMessageBox.critical(
                self,
                "Error!",
                f"You must provide article's title",
            )
            self.data = None  # Reset .data
            return
        for field in (self.titleField,
        self.authorsField,
        self.arxivIdField,
        self.versionField,
        self.datePublishedField,
        self.dateUpdatedField,
        self.linkField):
            self.data[field.objectName()] = field.text()

        if not self.data:
            return

        super().accept()

    