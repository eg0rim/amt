# -*- coding: utf-8 -*-
# amt/views/settingsdialog.py

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

"""settings dialog window"""

from PySide6.QtWidgets import (
    QDialog
)
from PySide6.QtCore import QSettings

from .build.settingsDialog_ui import Ui_Dialog
from amt.logger import getLogger

logger = getLogger(__name__)

class AMTSettingsDialog(QDialog):
    """
    Show settings dialog window with the options to change the application settings.
    """
    settingsFileName = "AMT/AMTSettings"
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.showPreviewOnStartCheckBox.setVisible(False)
        self.readSettings()
        
    def writeSettings(self):
        """
        Write settings to the settings file.
        """
        settings = QSettings(self.settingsFileName)
        settings.beginGroup("FileHandler")
        defAppFile = self.ui.defaultAppFileInput.filepath
        settings.setValue("defaultAppFile", defAppFile )
        pdfApp = self.ui.pdfFileInput.filepath
        settings.setValue("pdfApp", pdfApp)
        djvuApp = self.ui.djvuFileInput.filepath
        settings.setValue("djvuApp", djvuApp)
        logger.debug(f"Default app file: {defAppFile}, PDF app: {pdfApp}, Djvu app: {djvuApp}")
        openEntriesOnStartup = self.ui.entryOpenOnStartup.isChecked()
        settings.setValue("openEntriesOnStartup", openEntriesOnStartup)
        if openEntriesOnStartup:
            closeEntriesOnExit = self.ui.entryCloseOnExit.isChecked()
            settings.setValue("closeEntriesOnExit", closeEntriesOnExit)
        else:
            settings.setValue("closeEntriesOnExit", False)
        settings.endGroup()
        
        settings.beginGroup("LinkHandler")
        defLinkAppFile = self.ui.defaultLinkFileInput.filepath
        settings.setValue("defLinkApp", defLinkAppFile)
        httpLinkAppFile = self.ui.httpAppFileInput.filepath
        settings.setValue("httpApp", httpLinkAppFile)
        settings.endGroup()
        
        settings.beginGroup("Preview")
        settings.setValue("previewWidth", self.ui.previewWidthBox.value())
        settings.setValue("previewHeight", self.ui.previewHeightBox.value())
        #settings.setValue("showPreviewOnStartup", self.ui.showPreviewOnStartCheckBox.isChecked())
        settings.endGroup()
        
    def readSettings(self):
        """
        Read settings from the settings file.
        """
        settings = QSettings(self.settingsFileName)
        settings.beginGroup("FileHandler")
        defAppFile = settings.value("defaultAppFile", "")
        self.ui.defaultAppFileInput.filepath = defAppFile
        pdfApp = settings.value("pdfApp", "")
        self.ui.pdfFileInput.filepath = pdfApp
        djvuApp = settings.value("djvuApp", "")
        self.ui.djvuFileInput.filepath = djvuApp
        logger.debug(f"Default app file: {defAppFile}, PDF app: {pdfApp}, Djvu app: {djvuApp}")
        openEntriesOnStartup = settings.value("openEntriesOnStartup", False, type=bool)
        closeEntriesOnExit = settings.value("closeEntriesOnExit", False,type=bool)
        logger.debug(f"Open entries on startup: {openEntriesOnStartup}, Close entries on exit: {closeEntriesOnExit}")
        self.ui.entryOpenOnStartup.setChecked(openEntriesOnStartup)
        self.ui.entryCloseOnExit.setChecked(closeEntriesOnExit)
        settings.endGroup()
        
        settings.beginGroup("LinkHandler")
        defLinkAppFile = settings.value("defLinkApp")
        self.ui.defaultLinkFileInput.filepath = defLinkAppFile
        httpLinkAppFile = settings.value("httpApp")
        self.ui.httpAppFileInput.filepath = httpLinkAppFile
        settings.endGroup()
        
        settings.beginGroup("Preview")
        previewWidth = settings.value("previewWidth", 300, type=int)
        previewHeight = settings.value("previewHeight", 400, type=int)
        self.ui.previewWidthBox.setValue(previewWidth)
        self.ui.previewHeightBox.setValue(previewHeight)
        #showPreviewOnStartup = settings.value("showPreviewOnStartup", False, type=bool)
        #self.ui.showPreviewOnStartCheckBox.setChecked(showPreviewOnStartup)
        settings.endGroup()
        
    def accept(self):
        """
        Accept the changes, save settings and close the settings dialog window.
        """
        self.writeSettings()
        super().accept()