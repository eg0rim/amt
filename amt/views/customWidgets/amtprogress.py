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