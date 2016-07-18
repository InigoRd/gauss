#!/usr/bin/python
# -*- coding: utf-8 -*-
## File config.py
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

"""config module

Unused module
"""
class Config(object):
    """config.Config:
    
    Description:
        Config object
    Ancestry:
    +-- object
      +-- Config
    Atributes:
        "":
    Methods:
        
    """
    def __init__(self):
        self.__path = ""
    def _getPath(self):
        return self.__path
    def _setPath(self, path):
        self.__path = path
    path = property(_getPath, _setPath, None,
    """Base path where find all the program files needed""")
