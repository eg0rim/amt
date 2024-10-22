# -*- coding: utf-8 -*-
# amt/views/customWidgets/amtfiledialog.py

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

"""custom progress dialog"""

from PySide6.QtWidgets import QProgressDialog

from amt.logger import getLogger

logger = getLogger(__name__)

class AMTProgressDialog(QProgressDialog):
    """ 
    Customized QProgressDialog.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLabelText("Please wait...")
        self.setRange(0, 0)
        self.setMinimumDuration(0)
        self.setCancelButton(None)
        
        
class ArxivSearchProgressDialog(AMTProgressDialog):
    """
    Customized QProgressDialog for arXiv search.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLabelText("Searching arXiv...")
        self.setWindowTitle("Searching arXiv")
        
class FileDownloadProgressDialog(AMTProgressDialog):
    """
    Customized QProgressDialog for file download.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLabelText("Downloading file...")
        self.setWindowTitle("Downloading file")
        self.setRange(0, 100)
        
class MultiFileDownloadProgressDialog(FileDownloadProgressDialog):
    """
    Customized QProgressDialog for multiple file download.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLabelText("Downloading files...")
        self.setWindowTitle("Downloading files")
        self.setRange(0, 100)
        
    def setMultiValue(self, currentFile: int, totalFiles: int, progress: int):
        """
        Sets the value of the progress bar and denotes the current file being downloaded.
        """
        self.setValue(progress)
        self.setLabelText(f"Downloading files: {currentFile} of {totalFiles}...")