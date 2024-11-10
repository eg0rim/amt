# -*- coding: utf-8 -*-
# amt/views/customWidgets/amtmessagebox.py

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

"""custom message boxes"""

from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QIcon

from amt.views.build.resources_qrc import *

class AMTMessageBox(QMessageBox):
    """ 
    Custom message box for the Article Management Tool (AMT). Inherits from QMessageBox.
    All message box has the same title "Article Management Tool".
    Subclasses only differ by the icon.
    """
    def __init__(self, parent=None, text: str = None):
        super().__init__(parent)
        self.setWindowTitle("Article Management Tool")
        if text:
            self.setText(text)
        
class AMTInfoMessageBox(AMTMessageBox):
    def __init__(self, parent=None, text: str = None):
        super().__init__(parent, text)
        self.setIconPixmap(QIcon.fromTheme("information").pixmap(64, 64))
        
class AMTWarnMessageBox(AMTMessageBox):
    def __init__(self, parent=None, text: str = None):
        super().__init__(parent,text)
        self.setIconPixmap(QIcon.fromTheme("warning").pixmap(64, 64))
        
class AMTErrorMessageBox(AMTMessageBox):
    def __init__(self, parent=None, text: str = None):
        super().__init__(parent, text)
        self.setIconPixmap(QIcon.fromTheme("error").pixmap(64, 64))
        
class AMTMutliErrorMessageBox(AMTErrorMessageBox):
    def __init__(self, parent=None, text: str = None, errors: list[str] = None):
        super().__init__(parent, text)
        errorLines = "\n".join(f"{i+1}: {error}" for i, error in enumerate(errors))
        self.setInformativeText(errorLines) 
    
class AMTCriticalMessageBox(AMTMessageBox):
    def __init__(self, parent=None, text: str = None):
        super().__init__(parent, text)
        self.setIconPixmap(QIcon.fromTheme("error-red").pixmap(64, 64))
        
class AMTQuestionMessageBox(AMTMessageBox):
    def __init__(self, parent=None, text: str = None):
        super().__init__(parent,text)
        self.setIconPixmap(QIcon.fromTheme("question").pixmap(64, 64))
    