# -*- coding: utf-8 -*-
# amt/views/customWidgets/entryforms.py

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

"""afroms to add entriesa"""

from PySide6.QtWidgets import (
    QWidget
)

import amt.views.build.articleForm_ui as articleForm_ui
import amt.views.build.bookForm_ui as bookForm_ui
import amt.views.build.lecturesForm_ui as lecturesForm_ui
import amt.views.build.entryForm_ui as entryForm_ui
import amt.views.build.publishableForm_ui as publishableForm_ui
from amt.logger import getLogger
from amt.db.datamodel import (
    ArticleData,
    BookData,
    LecturesData,
    AuthorData,
    EntryData,
    PublishableData
)
from amt.views.customWidgets.amtmessagebox import (
    AMTInfoMessageBox
)

logger = getLogger(__name__)

class EntryForm(QWidget):
    """
    EntryForm is a QWidget subclass that serves as a base class for entry forms in the application.
    .ui file of all subclasses must be based on entryForm.ui.
    Class Attributes:
        dataType (type): The type of data the form is working with.
    Methods:
        __init__(parent=None)
        setupUi()
        fillEntryWithData(entry: EntryData)
        getData() -> EntryData
        setData(data: EntryData)
    """
    dataType = EntryData
    def __init__(self, parent=None):
        """
        Initializes the AbstractForm instance.
        """
        super().__init__(parent=parent)
        self.setupUi()
        
    def setupUi(self):
        """ 
        Sets up the UI components for the form.
        Must be reimplemented in subclasses.
        """
        self.ui = entryForm_ui.Ui_Form()
        self.ui.setupUi(self)
    
    def fillEntryWithData(self, entry: EntryData):
        """
        Fills the provided entry with data from the form.
        Args:
            entry (EntryData): The entry to fill with data.
        """
        title = self.ui.titleLineEdit.text()
        authorsStr = self.ui.authorLineEdit.text()
        authors = [AuthorData(name.strip()) for name in authorsStr.split(',')] if authorsStr else []
        entry.title = title
        entry.authors = authors
        entry.previewPage = self.ui.previewPageSpinBox.value()
        entry.fileName = self.ui.fileInput.getFilePath()
    
    def getData(self) -> EntryData:
        """
        Method to retrieve data from the form.
        Returns:
            EntryData: retrieved data from the form.
        """
        entry = self.dataType.createEmptyInstance()
        self.fillEntryWithData(entry)
        return entry

    def setData(self, data: EntryData):
        """
        Method to set data into the form.
        Args:
            data (EntryData): data to fill in the form.
        """
        self.ui.titleLineEdit.setText(data.title)
        self.ui.authorLineEdit.setText(', '.join([author.toString() for author in data.authors]))
        self.ui.previewPageSpinBox.setValue(data.previewPage)
        self.ui.fileInput.setFilePath(data.fileName)
        
class PublishableForm(EntryForm):
    """
    PublicationForm is a QWidget subclass that serves as a base class for publication forms in the application.
    .ui file of all subclasses must be based on publishableForm.ui.
    """ 
    dataType = PublishableData
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        
    def setupUi(self):
        self.ui = publishableForm_ui.Ui_Form()
        self.ui.setupUi(self)
        
    def fillEntryWithData(self, entry: PublishableData):
        super().fillEntryWithData(entry)
        entry.datePublished = self.ui.publishedDateInput.getDate()
        
    def setData(self, data: PublishableData):
        super().setData(data)
        self.ui.publishedDateInput.setDate(data.datePublished)   
    
class ArticleForm(PublishableForm):
    """
    A form for adding or editing an article entry.
    Implements PublicationForm.
    
    Methods:
        getMetadataFromArxiv()
    """
    dataType = ArticleData
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # connect get metadata button
        self.ui.getMetaButton.clicked.connect(self.getMetadataFromArxiv)
        
    def setupUi(self):
        self.ui = articleForm_ui.Ui_Form()
        self.ui.setupUi(self)
        
    def fillEntryWithData(self, entry: ArticleData):
        super().fillEntryWithData(entry)
        entry.arxivid = self.ui.arXivIDLineEdit.text()
        entry.version = self.ui.versionLineEdit.text()
        entry.journal = self.ui.journalLineEdit.text()
        entry.doi = self.ui.dOILineEdit.text()
        entry.link = self.ui.linkLineEdit.text()
        entry.dateArxivUploaded = self.ui.arxivUploadDatetimeInput.getDateTime()
        entry.dateArxivUpdated = self.ui.arxivUpdateDateTimeInput.getDateTime() 

    def setData(self, data: ArticleData):
        super().setData(data)
        self.ui.arXivIDLineEdit.setText(data.arxivid)
        self.ui.versionLineEdit.setText(data.version)
        self.ui.journalLineEdit.setText(data.journal)
        self.ui.dOILineEdit.setText(data.doi)
        self.ui.linkLineEdit.setText(data.link)
        self.ui.arxivUploadDatetimeInput.setDateTime(data.dateArxivUploaded)
        self.ui.arxivUpdateDateTimeInput.setDateTime(data.dateArxivUpdated)
        
    def getMetadataFromArxiv(self):
        """
        To be implemented in 0.2.0 version.
        Must retrieve metadata from arXiv based on the provided arXiv ID.
        """ 
        msgBox = AMTInfoMessageBox(self)
        msgBox.setText("This feature is not implemented yet.")
        msgBox.setInformativeText("It will be implemented in 0.2.0 version. Stay tuned!")
        msgBox.exec()
        
class BookForm(PublishableForm):
    """
    A form for adding or editing an book entry.
    Implements AbstractForm.
    """    
    dataType = BookData
    def __init__(self, parent=None):
        super().__init__(parent=parent)
    
    def setupUi(self):
        self.ui = bookForm_ui.Ui_Form()
        self.ui.setupUi(self)
        
    def fillEntryWithData(self, entry: BookData):
        super().fillEntryWithData(entry)
        entry.isbn = self.ui.iSBNLineEdit.text()
        entry.publisher = self.ui.publisherLineEdit.text()
    
    def setData(self, data: BookData):
        super().setData(data)
        self.ui.iSBNLineEdit.setText(data.isbn)
        self.ui.publisherLineEdit.setText(data.publisher)
        
class LecturesForm(PublishableForm):
    """
    A form for adding or editing an lecture notes entry.
    Implements AbstractForm.
    """
    dataType = LecturesData
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        
    def setupUi(self):
        self.ui = lecturesForm_ui.Ui_Form()
        self.ui.setupUi(self)
        
    def fillEntryWithData(self, entry: LecturesData):
        super().fillEntryWithData(entry)
        entry.course = self.ui.courseLineEdit.text()
        entry.school = self.ui.uniLineEdit.text()

    def setData(self, data: LecturesData):
        super().setData(data)
        self.ui.courseLineEdit.setText(data.course)
        self.ui.uniLineEdit.setText(data.school)
        