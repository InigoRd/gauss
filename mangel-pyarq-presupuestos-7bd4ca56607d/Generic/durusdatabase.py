#!/usr/bin/python
# -*- coding: utf-8 -*-
## File durus.py
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
import os.path
import time
# Durus Modules
from durus.file_storage import FileStorage
from durus.connection import Connection
# pyArq Presupuestos Modules
from Generic import utils
from Generic import globalVars
class DurusFile(object):
    def __init__(self, file, new):
        self.__file = file
        if new:
            if os.path.exists(self.__file):
                os.remove(self.__file)
        self.__connection = Connection(FileStorage(self.__file))
        self.__root = self.__connection.get_root()

    def close(self):
        self.__connection.get_storage().close()

    def getBudget(self):
        if self.__root.has_key("baseversion") and \
           globalVars.baseversion == self.__root["baseversion"]:
            return self.__root["budget"]
        else:
            print _("Incorrent Base version")
            return None

    def setBudget(self, budget):
        self.__root["budget"] = budget
        self.__root["baseversion"] = globalVars.baseversion
        self.__connection.commit()

class Read(object):
    def __init__(self, filename=None, budget=None):
        self.__budget = budget
        self.__filename = filename
        self.__cancel = False

    def cancel(self):
        """def cancel(self)
        
        It do nothing
        """
        # TODO: Cancel reading Durus database.
        self.__cancel = True
        
    def readFile(self, budget=None, filename=None, interface=None):
        if not filename is None:
            self.__filename = filename
        if self.__filename is None or self.__cancel == True:
            return None
        if not os.path.exists(self.__filename):
            return None
        print utils.mapping(_("Loading file: $1:"), (self.__filename,))
        _time = time.time()
        _durus_file = DurusFile(self.__filename, False)
        self.__budget = _durus_file.getBudget()
        _durus_file.close()
        print utils.mapping(_("Loadig time: $1 seconds"),
             (("%.2f" %(time.time()-_time)),))
        return self.__budget
