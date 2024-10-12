# -*- coding: utf-8 -*-
# amt/views/customWidgets/amtdatetime.py

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

"""custom datetime"""

from PySide6.QtWidgets import QDateTimeEdit, QWidget, QCheckBox, QHBoxLayout

class AMTDateTimeEdit(QDateTimeEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDisplayFormat("dd/MM/yyyy hh:mm:ss")
        
    def dateTime(self):
        if not self.isEnabled():
            return None
        return super().dateTime()
    
    def date(self):
        if not self.isEnabled():
            return None
        return super().date()
    
    def time(self):
        if not self.isEnabled():
            return None
        return super().time()

class AMTDateEdit(QDateTimeEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDisplayFormat("dd/MM/yyyy")
        
    def dateTime(self):
        if not self.isEnabled():
            return None
        return super().dateTime()
    
    def date(self):
        if not self.isEnabled():
            return None
        return super().date()
    
    def time(self):
        if not self.isEnabled():
            return None
        return super().time()
    
class AMTDateTimeInput(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dateTimeEdit = AMTDateTimeEdit(self)
        self.activeCheckBox = QCheckBox(self)
        self.setLayout(QHBoxLayout(self))
        self.layout().addWidget(self.activeCheckBox)
        self.layout().addWidget(self.dateTimeEdit)
        self.layout().setStretch(0, 0)
        self.layout().setStretch(1, 1)
        self.activeCheckBox.setChecked(False)
        self.dateTimeEdit.setEnabled(False)
        self.activeCheckBox.stateChanged.connect(self.dateTimeEdit.setEnabled)

class AMTDateInput(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dateEdit = AMTDateEdit(self)
        self.activeCheckBox = QCheckBox(self)
        self.setLayout(QHBoxLayout(self))
        self.layout().addWidget(self.activeCheckBox)
        self.layout().addWidget(self.dateEdit)
        self.layout().setStretch(0, 0)
        self.layout().setStretch(1, 1)
        self.activeCheckBox.setChecked(False)
        self.dateEdit.setEnabled(False)
        self.activeCheckBox.stateChanged.connect(self.dateEdit.setEnabled)