# -*- coding: utf-8 -*-
# amt/main.py

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

"""AMT application"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QCoreApplication
from amt.views.mainwindow import MainWindow
from amt.views.build.resources_qrc import *

def main():
    """
    Main function to initialize and run the Article Management Tool application.
    """
    # create the app
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(":/logo"))
    # set the app properties
    QCoreApplication.setOrganizationDomain("egorim.win")
    QCoreApplication.setApplicationName("Article Management Tool")
    QCoreApplication.setApplicationVersion("0.1.1")
    # create the main window
    win = MainWindow()
    # show main window
    win.show()
    # event loop
    sys.exit(app.exec_())