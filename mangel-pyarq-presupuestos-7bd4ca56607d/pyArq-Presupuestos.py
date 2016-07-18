#!/usr/bin/python
# -*- coding: utf-8 -*-
## File presupuestos.py
## This file is part of pyArq-Presupuestos.
##
## Copyright (C) 2010 Miguel Ángel Bárcena Rodríguez
##                         <miguelangel@obraencurso.es>
##
## pyArq-Presupuestos is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## pyArq-Presupuestos is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Modules
import sys
import gettext
# pyArq-Presupuestos modules
from Generic import globalVars
from Generic import win32Locale

def _take_APPDATA_path():
    # take path to find mo file
    _path = sys.path[0]
    globalVars.path["APPDATA"]= _path

def _translate():
    """def translate()
    
    Translates the program using gettext module
    """
    _app = "pyArq-Presupuestos"
    _dir = globalVars.path["APPDATA"] + "/mo/"
    if sys.platform == 'win32':
        win32Locale.check_win32_locale()
    gettext.install(_app, _dir, unicode=1)

def _run_gui():
    """def _run_gui
    
    Shows main window and starts the GTK+ event processing loop.
    """
    from Gtk import gui
    _window = gui.MainWindow()

# Run pyArq-Presupuestos
if __name__ == "__main__":
    _take_APPDATA_path()
    _translate()
    _run_gui()
