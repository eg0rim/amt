# -*- coding: utf-8 -*-
# amt/file_utils/linkhandler.py

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

"""Classes to operate with urls"""

from amt.logger import getLogger
import subprocess

logger = getLogger(__name__)

class LinkHandler:
    def __init__(self, defaultApp : str = "") -> None:
        self._defaultApp : str = defaultApp
        self._apps : dict[str, str] = {}
        
    @property
    def defaultApp(self):
        return self._defaultApp
    @defaultApp.setter
    def defaultApp(self, app: str):
        self._defaultApp = app
        
    def setApp(self, scheme : str, app : str):
        self._apps[scheme] = app
        
    @property
    def apps(self) -> dict[str, str]:
        """ """
        return self._apps
    @apps.setter
    def apps(self, apps: dict[str, str]):
        """ """
        self._apps = apps
        
    def openLink(self, url : str, application: str | None = None) -> bool:
        if application:
            app = application
        else:
            urlSplited = url.split(':')
            if len(urlSplited) < 2:
                app = self.defaultApp
                logger.warning("Scheme is not found, using default app.")
            else:
                scheme = urlSplited[0]
                try: 
                    app = self.apps[scheme]
                except KeyError:
                    pass
        if not app:
            app = self.defaultApp
        if not app:
            logger.error(f"Application to open the url {url} could not be inferred.")
            return False # may be raise exception
        try: 
            process = subprocess.Popen([app, url], stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)
            logger.debug(f"Opened url: {url} with application: {app},  process: {process}, pid: {process.pid}")   
            if process:
                return True
            else:
                return False
        except Exception as e: 
            logger.error(f"Failed to open url {url} with {app}, error: {e}")
            return False           