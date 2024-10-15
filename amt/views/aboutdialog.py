# -*- coding: utf-8 -*-
# amt/views/aboutdialog.py

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

"""about dialog window"""

from PySide6.QtWidgets import (
    QDialog
)
from .build.aboutDialog_ui import (
    Ui_AboutDialog
)

class AboutDialog(QDialog):
    """
    Show about dialog window with the information about the application.
    Includes attributions, license, and version.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)